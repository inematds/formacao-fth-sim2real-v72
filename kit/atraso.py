#!/usr/bin/env python3
"""atraso.py — o atraso entre a política e o motor: medir na bancada e ver o efeito na marcha.

Uso:
  python3 kit/atraso.py --medir            degrau no joelho com o robô pendurado: atraso do "real" × do "sim"
  python3 kit/atraso.py --ms 0 20 40       a política anda 10 s e leva 6 empurrões (120, 150 e 180 N por 0,2 s,
                                           para a frente e para o lado) com cada atraso: quantas quedas
O atraso é nativo do MuJoCo 3.5+ (atributo delay do atuador: o alvo chega ao PD N ms depois).
"""
import argparse

import mujoco
import numpy as np

import s2r

EMPURROES = [(f, d) for d in (0, 90) for f in (120, 150, 180)]


def degrau(pol, mundo):
    m = s2r.spec_bancada(pol, mundo).compile()
    d = s2r.iniciar(m, pol, fixo=True)
    j = m.joint("left_knee_joint")
    a = [i for i in range(m.nu) if m.actuator_trnid[i, 0] == j.id][0]
    q_ini = d.qpos[j.qposadr[0]]
    while d.time < 0.3:
        if d.time >= 0.1:
            d.ctrl[a] = pol.q0[a] + 0.3
        mujoco.mj_step(m, d)
        if d.time > 0.1 and d.qpos[j.qposadr[0]] - q_ini > 0.005:
            return d.time - 0.1
    return float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--medir", action="store_true")
    ap.add_argument("--ms", type=int, nargs="+", default=[0, 20, 40])
    a = ap.parse_args()
    pol = s2r.Politica()
    if a.medir:
        real = s2r.carregar_mundo("real")
        t_sim = degrau(pol, {})
        t_real = degrau(pol, {k: v for k, v in real.items() if k in ("atraso_ms",)})
        t_tudo = degrau(pol, real)
        print("degrau de 0,3 rad no joelho esquerdo, robô pendurado: tempo até o encoder mexer 0,005 rad")
        print(f"  sim:           {t_sim * 1000:5.0f} ms")
        print(f"  real:          {t_tudo * 1000:5.0f} ms")
        print(f"atraso medido (real − sim): {(t_tudo - t_sim) * 1000:.0f} ms")
        return 0
    print(f"atraso   quedas em {len(EMPURROES)} empurrões   (120/150/180 N, frente e lado, 0,2 s, t = 3 s)")
    for ms in a.ms:
        m = s2r.construir(pol, {"atraso_ms": ms})
        quedas = []
        for f, dr in EMPURROES:
            r = s2r.rodar(m, pol, empurrao=f, dir_emp=dr)
            quedas.append("x" if r["caiu"] is not None else ".")
        print(f"{ms:4d} ms  {quedas.count('x')}/{len(EMPURROES)}   {' '.join(quedas)}")
    print("(x = caiu, . = ficou de pé; ordem: 120, 150, 180 N para a frente e depois para o lado)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
