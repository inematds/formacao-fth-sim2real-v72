#!/usr/bin/env python3
"""randomizar.py — sorteia N mundos dentro de uma faixa e conta em quantos a política sobrevive 10 s andando.

Uso: python3 kit/randomizar.py --seeds 20 [--faixa treino|fora|<arquivo.json>] [--detalhe]
  treino = as faixas que o próprio treino da política randomizou (kit/mundos/treino.json)
  fora   = além do treino (kit/mundos/fora.json)
Cada faixa é [mín, máx]; "empurrao_vel" é a velocidade (m/s) que o empurrão dá ao robô em x e em y,
como o push_by_setting_velocity do Isaac Lab, aplicada aqui como força de 0,1 s no tronco, em t = 3 s.
Sem --faixa, roda as duas e compara.
"""
import argparse
import math

import numpy as np

import s2r

MASSA_G1 = 33.3  # kg, massa do modelo do Menagerie (curso 0, aula 2)


def sortear(faixa, rng):
    w = {}
    for k in ("atrito", "massa", "kp", "kd", "atraso_ms", "torque"):
        if k in faixa:
            lo, hi = faixa[k]
            w[k] = float(rng.uniform(lo, hi))
    if "atraso_ms" in w:
        w["atraso_ms"] = int(round(w["atraso_ms"] / 2) * 2)  # múltiplo do passo de 2 ms
    lo, hi = faixa.get("empurrao_vel", [0, 0])
    vx, vy = rng.uniform(lo, hi, 2)
    return w, float(vx), float(vy)


def rodar_faixa(nome, n, pol, detalhe=False):
    faixa = s2r.carregar_mundo(nome)
    rng = np.random.default_rng(7)  # semente fixa: o mesmo sorteio no seu computador
    vivos = 0
    for i in range(n):
        w, vx, vy = sortear(faixa, rng)
        f = math.hypot(vx, vy) * (MASSA_G1 + w.get("massa", 0)) / 0.1
        r = s2r.rodar(s2r.construir(pol, w), pol, empurrao=f, dur_emp=0.1, dir_emp=math.degrees(math.atan2(vy, vx)))
        vivos += r["caiu"] is None
        if detalhe:
            ps = " ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in w.items())
            print(f"  {i + 1:2d} {ps} empurrão {f:.0f} N → {'caiu' if r['caiu'] is not None else 'de pé'}")
    print(f"faixa {faixa['nome']:<7} sobreviveu: {vivos}/{n}")
    return vivos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--faixa")
    ap.add_argument("--detalhe", action="store_true")
    a = ap.parse_args()
    pol = s2r.Politica()
    faixas = [a.faixa] if a.faixa else ["treino", "fora"]
    for f in faixas:
        rodar_faixa(f, a.seeds, pol, a.detalhe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
