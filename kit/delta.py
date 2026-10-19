#!/usr/bin/env python3
"""delta.py — corrigir o simulador com dados do robô: um brinquedo linear da ideia do "delta action" (ASAP).

Uso: python3 kit/delta.py log.npz
O ASAP (RSS 2025, LeCAR-Lab/ASAP) treina por RL um modelo que soma uma ação corretiva ao comando dentro do
simulador até ele reproduzir as trajetórias do robô real, e depois ajusta a política nesse simulador corrigido.
Aqui, a mesma ideia em pequeno:
  - modelo de correção por junta da perna: δ = a·(alvo − q) + b·dq, recalculado a cada 20 ms (passo da política);
  - os 8 números (a e b de 4 juntas) são ajustados por mínimos quadrados (mujoco.minimize.least_squares) para
    que o simulador, repetindo o comando do log com a correção, chegue às posições que o robô mediu;
  - no fim, compara o erro sim × real com e sem a correção.
Diferença do ASAP: lá o modelo é uma rede treinada por RL com o estado inteiro; aqui são 8 coeficientes.
"""
import argparse

import numpy as np
from mujoco import minimize

import s2r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    a = ap.parse_args()
    pol = s2r.Politica()
    L = np.load(a.log)
    m = s2r.spec_bancada(pol, {}).compile()
    juntas = s2r.PERNA
    ij = [m.joint(j).qposadr[0] for j in juntas]
    iv = [m.joint(j).dofadr[0] for j in juntas]
    ia = [[i for i in range(m.nu) if m.actuator_trnid[i, 0] == m.joint(j).id][0] for j in juntas]
    n = len(juntas)

    def modelo(x):
        def corrigir(alvo, qpos, qvel):
            novo = alvo.copy()
            for c, ai in enumerate(ia):
                novo[ai] = alvo[ai] + x[c] * (alvo[ai] - qpos[ij[c]]) + x[n + c] * qvel[iv[c]]
            return novo
        return corrigir

    def residuo(X):
        if X.ndim == 1:
            return s2r.replay_bancada(pol, L, delta=modelo(X), vetor=True)
        return np.stack([s2r.replay_bancada(pol, L, delta=modelo(X[:, k]), vetor=True) for k in range(X.shape[1])], 1)

    x0 = np.zeros(2 * n)
    lim_inf, lim_sup = np.r_[-np.ones(n), -0.2 * np.ones(n)], np.r_[np.ones(n), 0.2 * np.ones(n)]
    x, _ = minimize.least_squares(x0, residuo, (lim_inf, lim_sup), eps=1e-4, verbose=0, max_iter=25)
    print(f"log: {a.log} · correção recalculada a cada 20 ms · δ = a·(alvo − q) + b·dq por junta")
    for c, j in enumerate(juntas):
        print(f"  {j.replace('_joint', ''):<18} a = {x[c]:+.2f}  b = {x[n + c]:+.3f}")
    antes = s2r.replay_bancada(pol, L)
    depois = s2r.replay_bancada(pol, L, delta=modelo(x))
    print(f"erro de rastreio sim × real: antes {antes:.2f}° → depois {depois:.2f}° (RMS das posições)")
    return 0 if depois < antes else 1


if __name__ == "__main__":
    raise SystemExit(main())
