#!/usr/bin/env python3
"""portao_sim2sim.py — o portão antes do robô: a política tem de passar em outro modelo e no caminho de mensagens.

Uso: python3 kit/portao_sim2sim.py [politica.onnx] [--passo 0.005] [--dds] [--ordem isaac|sdk]
  etapa 1  G1 do MuJoCo Menagerie (o modelo das aulas 1–5), PD dentro do MuJoCo
  etapa 2  G1 do unitree_mujoco (outro MJCF do mesmo robô, motores de torque), PD calculado a cada passo
  etapa 3  (--dds) o mesmo G1 do unitree_mujoco num processo separado, falando DDS como o robô de verdade:
           a política lê rt/lowstate e manda rt/lowcmd (domínio 1, interface lo), em tempo real
Critérios de cada etapa: não cair em 10 s andando a 0,5 m/s; velocidade média a ±0,15 m/s da pedida;
pernas e cintura no limite de torque em no máximo 1 % do tempo
(braço no limite sai como aviso: no simulador, o PD do punho, de 5 N·m e kd 10, oscila quando o passo é grande). Na etapa 3, também a frequência da política (≥ 45 Hz).
--ordem sdk reproduz o erro mais comum de sim2sim: ignorar o joint_ids_map do deploy.yaml.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

import mujoco
import numpy as np

import s2r

CMD, SEG, TOL = 0.5, 10.0, 0.15
CORPO = 15  # pernas (12) + cintura (3): os motores que seguram o peso, na ordem do robô


def julgar(nome, r, extra=""):
    motivos = []
    if r["caiu"] is not None:
        motivos.append(f"caiu em t = {r['caiu']:.1f} s")
    else:
        v = r["x"] / r["t"]
        if abs(v - CMD) > TOL:
            motivos.append(f"velocidade {v:.2f} m/s (pedida {CMD:.2f} ± {TOL:.2f})")
    sat = np.asarray(r["saturado"])
    if sat[:CORPO].max() > 0.01:
        motivos.append(f"pernas/cintura no limite de torque em {sat[:CORPO].max():.0%} do tempo (máx. 1 %)")
    ok = not motivos
    det = f"andou {r['x']:.1f} m" if r["caiu"] is None else f"andou {r['x']:.1f} m e caiu"
    print(f"{nome:<36} {'passou' if ok else 'reprovou'} · {det}{extra}" + ("" if ok else f" · {'; '.join(motivos)}"))
    if sat[CORPO:].max() > 0.01:
        print(f"{'':<36} aviso: braços no limite de torque em {sat[CORPO:].max():.0%} do tempo")
    return ok, motivos


def etapa_unitree_mujoco(pol, passo):
    """O G1 do unitree_mujoco (motores de torque) no mesmo processo, com o PD calculado a cada passo."""
    xml = s2r.RAIZ / "unitree_mujoco/unitree_robots/g1/scene_29dof.xml"
    if not xml.exists():
        s2r.erro(f"não achei {xml}. Rode a preparação da aula 6.")
    m = mujoco.MjModel.from_xml_path(str(xml))
    m.opt.timestep = passo  # o unitree_mujoco vem com SIMULATE_DT = 0.005
    d = mujoco.MjData(m)
    d.qpos[2] = 0.8
    d.qpos[7:7 + m.nu] = pol.q0
    mujoco.mj_forward(m, d)
    pol.reset()
    lim = np.abs(m.actuator_ctrlrange[:, 1])
    dec = int(round(s2r.PASSO_POLITICA / m.opt.timestep))
    caiu, sat, n = None, np.zeros(m.nu), 0
    for _ in range(int(round(SEG / s2r.PASSO_POLITICA))):
        alvo = pol.passo(d.qvel[3:6], d.qpos[3:7], (CMD, 0, 0), d.qpos[7:7 + m.nu], d.qvel[6:6 + m.nu])
        for _ in range(dec):
            tau = pol.kp * (alvo - d.qpos[7:7 + m.nu]) - pol.kd * d.qvel[6:6 + m.nu]
            sat += np.abs(tau) > lim
            n += 1
            d.ctrl[:] = np.clip(tau, -lim, lim)
            mujoco.mj_step(m, d)
        if d.qpos[2] < 0.5:
            caiu = d.time
            break
    return {"caiu": caiu, "x": float(d.qpos[0]), "t": float(d.time), "saturado": sat / max(n, 1)}


def etapa_dds(pol, passo):
    """Robô num processo (robo_dds.py), política neste, conversando por DDS como no robô real."""
    from unitree_sdk2py.core.channel import ChannelPublisher, ChannelSubscriber
    from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
    from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_, LowState_
    saida = Path(tempfile.mkdtemp()) / "robo.json"
    env = dict(os.environ, POSE_INICIAL=json.dumps(pol.q0.tolist()))
    robo = subprocess.Popen([sys.executable, str(s2r.KIT / "robo_dds.py"), "--seg", str(SEG + 0.5), "--saida", str(saida),
                             "--passo", str(passo)],
                            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    s2r.iniciar_dds(1, "lo")
    ultimo = {}
    sub = ChannelSubscriber("rt/lowstate", LowState_)
    sub.Init(lambda msg: ultimo.__setitem__("s", msg), 10)
    pub = ChannelPublisher("rt/lowcmd", LowCmd_)
    pub.Init()
    cmd = unitree_hg_msg_dds__LowCmd_()
    alvo = pol.q0.copy()
    trava = threading.Lock()
    rodando = True

    def enviar():  # o comando segue a ~500 Hz entre dois passos da política, como no robô
        while rodando:
            with trava:
                for i in range(pol.n):
                    mc = cmd.motor_cmd[i]
                    mc.mode, mc.q, mc.dq, mc.tau, mc.kp, mc.kd = 1, float(alvo[i]), 0.0, 0.0, float(pol.kp[i]), float(pol.kd[i])
            pub.Write(cmd)
            time.sleep(0.002)

    t0 = time.time()
    while "s" not in ultimo and time.time() - t0 < 15:
        time.sleep(0.01)
    if "s" not in ultimo:
        robo.kill()
        s2r.erro("nenhuma mensagem rt/lowstate em 15 s (DDS no domínio 1, interface lo). Rode a preparação da aula 6.")
    pol.reset()
    th = threading.Thread(target=enviar, daemon=True)
    th.start()
    passos, t_ini = 0, time.time()
    while time.time() - t_ini < SEG and robo.poll() is None:
        s = ultimo["s"]
        q = np.array([s.motor_state[i].q for i in range(pol.n)])
        dq = np.array([s.motor_state[i].dq for i in range(pol.n)])
        novo = pol.passo(np.array(s.imu_state.gyroscope), np.array(s.imu_state.quaternion), (CMD, 0, 0), q, dq)
        with trava:
            alvo[:] = novo
        passos += 1
        espera = t_ini + passos * s2r.PASSO_POLITICA - time.time()
        if espera > 0:
            time.sleep(espera)
    hz = passos / (time.time() - t_ini)
    try:
        robo.wait(timeout=20)
    finally:
        rodando = False
    if not saida.exists():
        s2r.erro("o processo do robô não gravou o resultado")
    r = json.load(open(saida))
    r["t"] = min(r["t"], SEG)
    if r["caiu"] is not None and r["caiu"] > SEG:  # o robô roda 0,5 s a mais; queda depois do fim não conta
        r["caiu"] = None
    return r, hz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("politica", nargs="?", help="pasta da política (padrão: a do unitree_rl_lab) ou o policy.onnx")
    ap.add_argument("--dds", action="store_true")
    ap.add_argument("--ordem", default="isaac", choices=["isaac", "sdk"])
    ap.add_argument("--passo", type=float, default=0.005, help="passo do unitree_mujoco (s); o dele é 0.005")
    a = ap.parse_args()
    pasta = s2r.POLITICA
    if a.politica:
        p = Path(a.politica)
        pasta = p.parents[1] if p.suffix == ".onnx" else p
    pol = s2r.Politica(pasta, ordem=a.ordem)
    print(f"política: {pasta.name if pasta != s2r.POLITICA else 'unitree_rl_lab velocity v0'} · ordem das juntas: {a.ordem} · {CMD} m/s por {SEG:.0f} s")
    resultados = []
    r1 = s2r.rodar(s2r.construir(pol), pol, cmd=(CMD, 0, 0), seg=SEG)
    resultados.append(julgar("1 Menagerie (MuJoCo, PD no MJCF)", r1))
    r2 = etapa_unitree_mujoco(pol, a.passo)
    resultados.append(julgar(f"2 unitree_mujoco (passo {a.passo * 1000:.0f} ms)", r2))
    if a.dds:
        r3, hz = etapa_dds(pol, a.passo)
        ok, mot = julgar("3 unitree_mujoco + DDS (tempo real)", r3, f" · política a {hz:.0f} Hz")
        if hz < 45:
            ok, mot = False, mot + [f"política a {hz:.0f} Hz (< 45)"]
            print(f"{'':<34} reprovou · laço lento")
        resultados.append((ok, mot))
    falhas = [m for ok, ms in resultados if not ok for m in ms]
    if falhas:
        print(f"PORTÃO: reprovou — {falhas[0]}")
        return 1
    print(f"PORTÃO: passou ({len(resultados)} de {len(resultados)} etapas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
