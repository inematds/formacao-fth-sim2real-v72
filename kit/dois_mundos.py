#!/usr/bin/env python3
"""dois_mundos.py — a mesma política de marcha do G1 em dois mundos: "sim" e "real simulado".

Uso: python3 kit/dois_mundos.py [--so atrito|massa|kp|atraso_ms] [--kp-comando X]
  --so P           o "real" troca só o parâmetro P (o resto fica como no sim): ache o culpado
  --kp-comando X   multiplica o kp que o controlador manda (compensação da aula 4)
O "real simulado" é kit/mundos/real.json: um MuJoCo com parâmetros escondidos, dito como tal.
"""
import argparse

import s2r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--so", choices=["atrito", "massa", "kp", "atraso_ms"])
    ap.add_argument("--kp-comando", type=float, default=1.0)
    ap.add_argument("--vel", type=float, default=0.5)
    a = ap.parse_args()
    pol = s2r.Politica()
    real = s2r.carregar_mundo("real")
    if a.so:
        real = {a.so: real[a.so]}
    mundos = [("sim", {}), ("real simulado" + (f" (só {a.so})" if a.so else ""), real)]
    print(f"política: unitree_rl_lab G1 29 GDL velocity v0 (ONNX, {pol.dim_obs} entradas) · comando {a.vel:.2f} m/s · 10 s")
    falhas = 0
    for nome, w in mundos:
        w = dict(w)
        if a.kp_comando != 1.0:
            w["kp"] = w.get("kp", 1.0) * a.kp_comando
        r = s2r.rodar(s2r.construir(pol, w), pol, cmd=(a.vel, 0, 0))
        falhas += r["caiu"] is not None
        print(f"{nome:<28} {s2r.resumo(r, a.vel)}")
    return 1 if falhas else 0


if __name__ == "__main__":
    raise SystemExit(main())
