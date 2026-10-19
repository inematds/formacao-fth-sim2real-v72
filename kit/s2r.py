"""s2r.py — funções comuns do kit do curso FTH 2 (Do simulador ao chão).

A "política" das práticas é a política de velocidade do Unitree G1 29 GDL que a Unitree publica pronta no
unitree_rl_lab (treinada no Isaac Lab, exportada em ONNX, Apache-2.0). O kit a roda no MuJoCo com o G1 do
MuJoCo Menagerie: isso já é um sim2sim (Isaac Lab → MuJoCo).

Bancada: $FTH (padrão ~/fth) com .venv, mujoco_menagerie (62ab00f) e unitree_rl_lab (4960b84).
Testado com mujoco 3.16.0, onnxruntime 1.31.0, numpy 2.5.4, Python 3.12, aarch64, 19/10/2026.
"""
import json
import math
import os
import sys
from pathlib import Path

import mujoco
import numpy as np

KIT = Path(__file__).resolve().parent
RAIZ = Path(os.environ.get("FTH", KIT.parents[1]))
MENAGERIE = RAIZ / "mujoco_menagerie"
G1 = MENAGERIE / "unitree_g1" / "scene.xml"
POLITICA = RAIZ / "unitree_rl_lab" / "deploy/robots/g1_29dof/config/policy/velocity/v0"
MUNDOS = KIT / "mundos"
PASSO_POLITICA = 0.02  # 50 Hz, o step_dt do deploy.yaml


def erro(msg):
    sys.exit(f"ERRO: {msg}")


def ler_yaml(p):
    import yaml
    return yaml.safe_load(open(p))


class Politica:
    """Política ONNX + as regras do deploy.yaml: ordem das juntas, ganhos, pose padrão, escalas e histórico.

    ordem="isaac" (certo): a lista joint_ids_map traduz a ordem do Isaac Lab para a ordem do robô (SDK/MJCF).
    ordem="sdk" (o erro comum): usa a pose padrão e as ações como se já estivessem na ordem do robô.
    """

    def __init__(self, pasta=POLITICA, ordem="isaac"):
        cfg_p = Path(pasta) / "params/deploy.yaml"
        onnx_p = Path(pasta) / "exported/policy.onnx"
        if not onnx_p.exists():
            erro(f"não achei {onnx_p}. Rode a preparação da aula 1 (unitree_rl_lab no sparse-checkout).")
        import onnxruntime as ort
        so = ort.SessionOptions()
        so.intra_op_num_threads = 1
        so.inter_op_num_threads = 1
        self.sess = ort.InferenceSession(str(onnx_p), so, providers=["CPUExecutionProvider"])
        self.inp = self.sess.get_inputs()[0].name
        c = ler_yaml(cfg_p)
        n = len(c["joint_ids_map"])
        self.n = n
        self.mapa = np.array(c["joint_ids_map"], dtype=int) if ordem == "isaac" else np.arange(n)
        self.kp = np.array(c["stiffness"], float)   # já na ordem do robô
        self.kd = np.array(c["damping"], float)
        self.q0 = np.zeros(n)
        self.q0[self.mapa] = c["default_joint_pos"]  # o yaml traz a pose padrão na ordem do Isaac Lab
        self.escala = np.array(c["actions"]["JointPositionAction"]["scale"], float)
        ob = c["observations"]
        self.h = ob["base_ang_vel"]["history_length"]
        self.esc_w = ob["base_ang_vel"]["scale"][0]
        self.esc_dq = ob["joint_vel_rel"]["scale"][0]
        self.dim_obs = self.sess.get_inputs()[0].shape[1]
        self.reset()

    def reset(self):
        self.ultima = np.zeros(self.n)
        self.hist = None

    def passo(self, w_corpo, quat_wxyz, cmd, q, dq):
        """Recebe o estado na ordem do robô e devolve o alvo de posição de cada junta (ordem do robô)."""
        g = np.zeros(3)
        qw, qx, qy, qz = quat_wxyz
        mujoco.mju_rotVecQuat(g, np.array([0.0, 0.0, -1.0]), np.array([qw, -qx, -qy, -qz]))
        termos = [np.asarray(w_corpo) * self.esc_w, g, np.asarray(cmd, float),
                  (q - self.q0)[self.mapa], np.asarray(dq)[self.mapa] * self.esc_dq, self.ultima]
        if self.hist is None:
            self.hist = [[t.copy()] * self.h for t in termos]
        else:
            for i, t in enumerate(termos):
                self.hist[i] = self.hist[i][1:] + [t.copy()]
        obs = np.concatenate([np.concatenate(h) for h in self.hist]).astype(np.float32)[None]
        a = self.sess.run(None, {self.inp: obs})[0][0].astype(float)
        self.ultima = a
        alvo = self.q0.copy()
        alvo[self.mapa] = a * self.escala + self.q0[self.mapa]
        return alvo


def carregar_mundo(nome_ou_caminho):
    p = Path(nome_ou_caminho)
    if not p.exists():
        p = MUNDOS / f"{nome_ou_caminho}.json"
    if not p.exists():
        erro(f"mundo {nome_ou_caminho} não existe (veja kit/mundos/)")
    return json.load(open(p))


def aplicar_ganhos(s, pol, kpx=1.0, kdx=1.0, atraso_ms=0.0, so=None):
    """Põe o PD da política nos atuadores do spec. so = nomes das juntas a mexer (padrão: todas)."""
    dt = s.option.timestep
    atraso = atraso_ms / 1000.0
    for i, a in enumerate(s.actuators):
        if so is not None and a.target not in so:
            continue
        a.gainprm[0] = pol.kp[i] * kpx
        a.biasprm[0] = 0.0
        a.biasprm[1] = -pol.kp[i] * kpx
        a.biasprm[2] = -pol.kd[i] * kdx
        a.ctrllimited = 0
        if atraso > 0:
            a.delay = atraso
            a.nsample = int(math.ceil(atraso / dt)) + 2


def spec_g1(pol, mundo=None, fixo=False):
    """Spec do G1 do Menagerie com o PD da política dentro do MuJoCo (atuador de posição: kp e kd do deploy.yaml).

    mundo: atrito (×), massa (kg somados ao tronco), kp (×), kd (×), atraso_ms (alvo chega atrasado),
           torque (× o limite de torque das juntas). fixo=True pendura o robô pela pelve (pórtico).
    """
    mundo = mundo or {}
    if not G1.exists():
        erro(f"não achei {G1}. Rode a preparação da aula 1 (Menagerie com unitree_g1).")
    s = mujoco.MjSpec.from_file(str(G1))
    for g in s.geoms:
        g.friction[0] *= mundo.get("atrito", 1.0)
    if mundo.get("massa"):
        s.body("torso_link").mass += mundo["massa"]
    aplicar_ganhos(s, pol, mundo.get("kp", 1.0), mundo.get("kd", 1.0), mundo.get("atraso_ms", 0))
    for j in s.joints:
        if j.actfrclimited:
            j.actfrcrange[0] *= mundo.get("torque", 1.0)
            j.actfrcrange[1] *= mundo.get("torque", 1.0)
    if fixo:
        pelve = s.body("pelvis")
        for j in list(pelve.joints):
            if j.type == mujoco.mjtJoint.mjJNT_FREE:
                s.delete(j)
        pelve.pos = [0, 0, 1.2]
        for k in list(s.keys):
            s.delete(k)
    return s


def construir(pol, mundo=None, fixo=False):
    return spec_g1(pol, mundo, fixo).compile()


# --- bancada do pórtico (aulas 3 e 5): robô pendurado, perna esquerda balança, encoders medem ---
PERNA = ["left_hip_pitch_joint", "left_hip_roll_joint", "left_knee_joint", "left_ankle_pitch_joint"]
AMPL = {"left_hip_pitch_joint": 0.35, "left_hip_roll_joint": 0.15, "left_knee_joint": 0.45, "left_ankle_pitch_joint": 0.2}


def spec_bancada(pol, mundo=None, historico=0):
    """historico > 0: guarda N comandos nos atuadores da perna (o sysid ajusta o atraso sem mudar o tamanho do estado)."""
    s = spec_g1(pol, mundo, fixo=True)
    for sen in list(s.sensors):  # a bancada só lê os encoders da perna (a IMU do tronco não mexe: a pelve está presa)
        s.delete(sen)
    if historico:
        for a in s.actuators:
            if a.target in PERNA:
                a.nsample = historico
                a.interp = 1
    for prefixo, tipo in (("enc_", mujoco.mjtSensor.mjSENS_JOINTPOS), ("vel_", mujoco.mjtSensor.mjSENS_JOINTVEL)):
        for j in PERNA:
            sen = s.add_sensor()
            sen.name = prefixo + j.replace("_joint", "")
            sen.type = tipo
            sen.objtype = mujoco.mjtObj.mjOBJ_JOINT
            sen.objname = j
    return s


def sinal_bancada(m, pol, seg=4.0, fase=0.0):
    """Alvo de posição de cada junta a cada passo: pose padrão + varredura de frequência (0,5 → 3 Hz) na perna."""
    n = int(round(seg / m.opt.timestep))
    t = np.arange(n) * m.opt.timestep
    f = 0.5 + (3.0 - 0.5) * t / seg
    ctrl = np.tile(pol.q0, (n, 1))
    for k, j in enumerate(PERNA):
        a = [i for i in range(m.nu) if m.actuator_trnid[i, 0] == m.joint(j).id][0]
        ctrl[:, a] += AMPL[j] * np.sin(2 * np.pi * f * t + fase + k)
    return t, ctrl


def estado(m, d, fixo=False):
    if fixo:
        return np.zeros(3), np.array([1.0, 0, 0, 0]), d.qpos.copy(), d.qvel.copy()
    return d.qvel[3:6].copy(), d.qpos[3:7].copy(), d.qpos[7:].copy(), d.qvel[6:].copy()


def encher_historico(m, d):
    """Atuador com atraso guarda os últimos comandos; no início, o buffer vem zerado. Enche com o ctrl atual."""
    for a in range(m.nu):
        n = int(m.actuator_history[a, 0])
        if n > 0:
            mujoco.mj_initCtrlHistory(m, d, a, None, np.full((n, 1), d.ctrl[a]))


def iniciar(m, pol, fixo=False):
    d = mujoco.MjData(m)
    if fixo:
        d.qpos[:] = pol.q0
    else:
        d.qpos[2] = 0.8
        d.qpos[7:] = pol.q0
    d.ctrl[:] = pol.q0
    encher_historico(m, d)
    mujoco.mj_forward(m, d)
    return d


def rodar(m, pol, cmd=(0.5, 0.0, 0.0), seg=10.0, empurrao=0.0, t_emp=3.0, dur_emp=0.2, dir_emp=0.0,
          compensar=None, registrar=False):
    """Roda a política por `seg` segundos. Queda = pelve abaixo de 0,5 m.

    empurrao: força (N) no tronco por dur_emp s a partir de t_emp, na direção dir_emp (graus; 0 = para a frente).
    compensar(alvo, q, dq) -> alvo: correção aplicada ao comando antes de mandar ao robô (aula 5).
    """
    pol.reset()
    d = iniciar(m, pol)
    dec = int(round(PASSO_POLITICA / m.opt.timestep))
    tronco = m.body("torso_link").id
    ang = math.radians(dir_emp)
    fx, fy = math.cos(ang) * empurrao, math.sin(ang) * empurrao
    log = {"q": [], "dq": [], "alvo": [], "q1": [], "dq1": []}
    caiu = None
    tq_max, sat, passos = 0.0, np.zeros(m.nu), 0
    lim = np.array([m.jnt_actfrcrange[m.actuator_trnid[a, 0]][1] for a in range(m.nu)])
    for _ in range(int(round(seg / PASSO_POLITICA))):
        w, quat, q, dq = estado(m, d)
        alvo = pol.passo(w, quat, cmd, q, dq)
        if compensar is not None:
            alvo = compensar(alvo, q, dq)
        d.ctrl[:] = alvo
        for _ in range(dec):
            ativo = empurrao and t_emp <= d.time < t_emp + dur_emp
            d.xfrc_applied[tronco, 0] = fx if ativo else 0.0
            d.xfrc_applied[tronco, 1] = fy if ativo else 0.0
            mujoco.mj_step(m, d)
            frac = np.abs(d.actuator_force) / lim
            tq_max = max(tq_max, float(frac.max()))
            sat += frac > 1.0
            passos += 1
        if registrar:
            log["q"].append(q); log["dq"].append(dq); log["alvo"].append(alvo)
            log["q1"].append(d.qpos[7:].copy()); log["dq1"].append(d.qvel[6:].copy())
        if d.qpos[2] < 0.5:
            caiu = d.time
            break
    t = d.time
    r = {"caiu": caiu, "t": t, "x": float(d.qpos[0]), "y": float(d.qpos[1]),
         "vel": float(d.qpos[0] / t) if t > 0 else 0.0, "torque_max": tq_max,
         "saturado": sat / max(passos, 1)}  # fração do tempo no limite, por motor
    if registrar:
        r["log"] = {k: np.array(v) for k, v in log.items()}
    return r


def resumo(r, cmd=0.5):
    if r["caiu"] is not None:
        return f"queda: sim em t = {r['caiu']:.1f} s (andou {r['x']:.1f} m)"
    return f"queda: não · andou {r['x']:.1f} m em {r['t']:.0f} s (vel. {r['vel']:.2f} m/s; pedida {cmd:.2f})"


def replay_bancada(pol, L, mundo=None, delta=None, vetor=False):
    """Repete na bancada simulada o comando gravado no log e devolve o erro RMS (graus) das posições medidas.

    delta(alvo, q, dq) -> alvo corrigido, aplicado a cada 20 ms (aula 5)."""
    m = spec_bancada(pol, mundo or {}).compile()
    d = iniciar(m, pol, fixo=True)
    nomes = [str(n) for n in L["nomes"]]
    enc = [i for i, n in enumerate(nomes) if n.startswith("enc_")]
    adr = [m.sensor(nomes[i]).adr[0] for i in enc]
    dec = int(round(PASSO_POLITICA / m.opt.timestep))
    pred, corr = [], np.zeros(m.nu)
    for k in range(len(L["t"])):
        if delta is not None and k % dec == 0:
            corr = delta(L["ctrl"][k], d.qpos.copy(), d.qvel.copy()) - L["ctrl"][k]
        d.ctrl[:] = L["ctrl"][k] + corr
        mujoco.mj_step(m, d)
        pred.append(d.sensordata[adr].copy())
    err = np.array(pred) - L["sensores"][:, enc]
    if vetor:
        return err.ravel()
    return float(np.degrees(np.sqrt(np.mean(err ** 2))))


def iniciar_dds(dominio=1, interface="lo"):
    """Abre o DDS da Unitree (unitree_sdk2py) no domínio e na interface dados.

    A interface lo não faz multicast; sem multicast, dois processos não se descobrem. Aqui a descoberta vai por
    unicast para 127.0.0.1 (bloco Discovery/Peers da configuração do CycloneDDS), só quando a interface é lo."""
    import unitree_sdk2py.core.channel as ch
    if interface == "lo" and "<Peers>" not in ch.ChannelConfigHasInterface:
        ch.ChannelConfigHasInterface = ch.ChannelConfigHasInterface.replace(
            "</General>", "</General><Discovery><ParticipantIndex>auto</ParticipantIndex>"
            "<MaxAutoParticipantIndex>20</MaxAutoParticipantIndex>"
            "<Peers><Peer address=\"127.0.0.1\"/></Peers></Discovery>")
    ch.ChannelFactoryInitialize(dominio, interface)
