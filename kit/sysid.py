#!/usr/bin/env python3
"""sysid.py — identificação de sistema: ajusta o modelo do MuJoCo até ele reproduzir o ensaio de bancada.

Uso: python3 kit/sysid.py log.npz [--parametros kp,kd|kp] [--revelar]
Usa o toolbox mujoco.sysid (MuJoCo 3.5+; aqui 3.16.0, pip install "mujoco[sysid]==3.16.0"): parte do modelo
nominal (kp = 1,0 × o do deploy.yaml, sem atraso), simula o mesmo comando do log e minimiza a diferença entre os
encoders simulados e os medidos (mínimos quadrados não lineares).
--revelar abre kit/mundos/real.json no fim e compara com o valor escondido.
"""
import argparse
import contextlib
import io
import logging

import mujoco
import numpy as np

import s2r

FAIXAS = {"kp": (1.0, 0.3, 1.5), "kd": (1.0, 0.3, 3.0)}  # nominal, mín, máx (× o valor do deploy.yaml)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("log")
    ap.add_argument("--parametros", default="kp,kd")
    ap.add_argument("--revelar", action="store_true")
    a = ap.parse_args()
    logging.disable(logging.WARNING)
    from mujoco import sysid
    pol = s2r.Politica()
    L = np.load(a.log)
    spec = s2r.spec_bancada(pol, {})
    m = spec.compile()
    nomes = [str(n) for n in L["nomes"]]
    perna = s2r.PERNA

    def mexer(nome):
        def f(s, p):
            v = float(p.value[0])
            for i, at in enumerate(s.actuators):
                if at.target not in perna:
                    continue
                if nome == "kp":
                    at.gainprm[0] = pol.kp[i] * v
                    at.biasprm[1] = -pol.kp[i] * v
                elif nome == "kd":
                    at.biasprm[2] = -pol.kd[i] * v
        return f

    params = sysid.ParameterDict()
    escolhidos = [p.strip() for p in a.parametros.split(",") if p.strip()]
    for nome in escolhidos:
        nom, lo, hi = FAIXAS[nome]
        params.add(sysid.Parameter(nome, nominal=nom, min_value=lo, max_value=hi, modifier=mexer(nome)))
    d = s2r.iniciar(m, pol, fixo=True)
    est = np.empty(mujoco.mj_stateSize(m, mujoco.mjtState.mjSTATE_FULLPHYSICS))
    mujoco.mj_getState(m, d, est, mujoco.mjtState.mjSTATE_FULLPHYSICS)
    ctrl_ts = sysid.TimeSeries.from_control_names(np.concatenate([[0.0], L["t"]]), np.vstack([L["ctrl"], L["ctrl"][-1:]]), m)
    sen_ts = sysid.TimeSeries.from_names(L["t"], L["sensores"], m, names=nomes)
    ms = sysid.ModelSequences("g1_bancada", spec, "varredura", est, ctrl_ts, sen_ts)
    res = sysid.build_residual_fn(models_sequences=[ms], n_threads=1)
    r0 = np.concatenate(res(params.as_vector(), params)[0])
    with contextlib.redirect_stdout(io.StringIO()):  # o otimizador imprime cada iteração
        opt, out = sysid.optimize(initial_params=params, residual_fn=res, optimizer="mujoco", verbose=False)
    r1 = np.concatenate(res(opt.as_vector(), opt)[0])
    print(f"log: {a.log} · {len(L['t'])} amostras · sinais: {len(nomes)} (posição e velocidade de {len(nomes) // 2} juntas)")
    print(f"resíduo, modelo nominal:      {np.sqrt(np.mean(r0 ** 2)):6.3f}")
    print(f"resíduo, modelo identificado: {np.sqrt(np.mean(r1 ** 2)):6.3f}")
    ident = {n: float(opt[n].value[0]) for n in escolhidos}
    print(f"erro das posições na bancada, modelo nominal:      {s2r.replay_bancada(pol, L):5.2f}° (RMS)")
    print(f"erro das posições na bancada, modelo identificado: {s2r.replay_bancada(pol, L, ident):5.2f}° (RMS)")
    for nome in escolhidos:
        print(f"{nome:<10} nominal {FAIXAS[nome][0]:6.2f} → identificado {float(opt[nome].value[0]):6.2f}")
    if a.revelar:
        real = s2r.carregar_mundo("real")
        ok = True
        for nome in escolhidos:
            esc = real.get(nome, FAIXAS[nome][0])
            v = float(opt[nome].value[0])
            dentro = abs(v - esc) <= 0.1 * abs(esc) if esc else abs(v) < 2.0
            ok &= dentro
            print(f"{nome:<10} escondido {esc:6.2f} · dentro de ±10 %: {'sim' if dentro else 'não'}")
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
