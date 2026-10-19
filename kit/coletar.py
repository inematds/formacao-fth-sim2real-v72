#!/usr/bin/env python3
"""coletar.py — ensaio de bancada: o G1 pendurado no pórtico balança a perna esquerda e grava os encoders.

Uso: python3 kit/coletar.py [--mundo real|sim] [--saida log.npz]
É o que se faz no robô de verdade antes de identificar o atuador: robô suspenso, pés no ar, uma varredura de
frequência (0,5 → 3 Hz) no quadril, no joelho e no tornozelo, 4 s, encoders e velocidades lidos a 500 Hz, com ruído de 0,002 rad e 0,02 rad/s.
Aqui o "robô de verdade" é o mundo kit/mundos/real.json (um MuJoCo com parâmetros escondidos).
"""
import argparse

import mujoco
import mujoco.rollout as rollout
import numpy as np

import s2r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mundo", default="real")
    ap.add_argument("--saida", default="log.npz")
    a = ap.parse_args()
    pol = s2r.Politica()
    m = s2r.spec_bancada(pol, s2r.carregar_mundo(a.mundo)).compile()
    d = s2r.iniciar(m, pol, fixo=True)
    t, ctrl = s2r.sinal_bancada(m, pol)
    est = np.empty(mujoco.mj_stateSize(m, mujoco.mjtState.mjSTATE_FULLPHYSICS))
    mujoco.mj_getState(m, d, est, mujoco.mjtState.mjSTATE_FULLPHYSICS)
    _, sen = rollout.rollout(m, d, est, ctrl[:-1])
    sen = np.squeeze(sen, 0)
    nomes = [m.sensor(i).name for i in range(m.nsensor)]  # enc_* (posição) e vel_* (velocidade)
    rng = np.random.default_rng(3)
    ruido = np.array([0.002 if n.startswith("enc_") else 0.02 for n in nomes])  # rad e rad/s
    med = sen + rng.normal(0, 1, sen.shape) * ruido
    np.savez(a.saida, t=t[1:], ctrl=ctrl[:-1], sensores=med, nomes=np.array(nomes), q0=pol.q0)
    enc = med[:, [i for i, n in enumerate(nomes) if n.startswith("enc_")]]
    nomes = [n for n in nomes if n.startswith("enc_")]
    amp = np.degrees(enc.max(0) - enc.min(0))
    print(f"ensaio de bancada no mundo '{a.mundo}': {len(t) - 1} amostras em {t[-1]:.1f} s · {len(nomes)} encoders + velocidades")
    for n, v in zip(nomes, amp):
        print(f"  {n:<22} amplitude medida {v:5.1f}°")
    print(f"gravado: {a.saida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
