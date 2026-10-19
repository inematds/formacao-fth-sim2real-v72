#!/usr/bin/env python3
"""robo_dds.py — o "robô" do portão sim2sim: o G1 do unitree_mujoco com a ponte DDS da Unitree.

Uso (o portao_sim2sim.py --dds abre sozinho): python3 kit/robo_dds.py --seg 12 --saida robo.json
Publica rt/lowstate e escuta rt/lowcmd (domínio DDS 1, interface lo), como o robô de verdade faz na rede.
Espera o primeiro comando antes de soltar a física, roda em tempo real e grava o resultado em JSON.
Sem tela: não abre o visualizador.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import mujoco
import numpy as np

RAIZ = Path(os.environ.get("FTH", Path(__file__).resolve().parents[2]))
UM = RAIZ / "unitree_mujoco"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seg", type=float, default=12.0)
    ap.add_argument("--saida", default="robo.json")
    ap.add_argument("--passo", type=float, default=0.005)
    a = ap.parse_args()
    if not (UM / "simulate_python").exists():
        sys.exit(f"ERRO: não achei {UM}. Rode a preparação da aula 6.")
    sys.path.insert(0, str(UM / "simulate_python"))
    import config
    config.ROBOT, config.USE_JOYSTICK, config.ENABLE_ELASTIC_BAND = "g1", 0, False
    config.SIMULATE_DT = a.passo
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import s2r
    s2r.iniciar_dds(config.DOMAIN_ID, config.INTERFACE)
    from unitree_sdk2py_bridge import UnitreeSdk2Bridge

    m = mujoco.MjModel.from_xml_path(str(UM / "unitree_robots/g1/scene_29dof.xml"))
    m.opt.timestep = config.SIMULATE_DT
    d = mujoco.MjData(m)
    q0 = np.array(json.loads(os.environ.get("POSE_INICIAL", "[]")) or np.zeros(m.nu))
    d.qpos[2] = 0.8
    d.qpos[7:7 + m.nu] = q0
    mujoco.mj_forward(m, d)
    ponte = UnitreeSdk2Bridge(m, d)
    t0 = time.time()
    while not np.any(d.ctrl) and time.time() - t0 < 10:  # espera o controlador mandar o 1º comando
        time.sleep(0.005)
    caiu, lim = None, np.abs(m.actuator_ctrlrange[:, 1])
    sat, por_motor, passos, t_ini = 0, np.zeros(m.nu), 0, time.time()
    while d.time < a.seg:
        alvo = t_ini + d.time
        mujoco.mj_step(m, d)
        passos += 1
        no_limite = np.abs(d.ctrl) > lim
        sat += bool(no_limite.any())
        por_motor += no_limite
        if caiu is None and d.qpos[2] < 0.5:
            caiu = d.time
        espera = alvo + m.opt.timestep - time.time()
        if espera > 0:
            time.sleep(espera)
    r = {"caiu": caiu, "x": float(d.qpos[0]), "t": float(d.time), "passos": passos,
         "parede_s": time.time() - t_ini, "saturado": (por_motor / max(passos, 1)).tolist(),
         "motores_no_limite": {m.actuator(i).name: round(float(por_motor[i] / max(passos, 1)), 3)
                               for i in range(m.nu) if por_motor[i] / max(passos, 1) > 0.01}}
    json.dump(r, open(a.saida, "w"))
    del ponte
    os._exit(0)  # as threads da ponte não terminam sozinhas


if __name__ == "__main__":
    main()
