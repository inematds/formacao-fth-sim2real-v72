#!/usr/bin/env python3
"""conferir_escada.py — confere a sua escada de implantação (aula 8).

Uso: python3 kit/conferir_escada.py escada.yaml
Exige os 4 degraus na ordem sim → sim2sim → suspenso → chão, cada um com "onde", "criterio" e "parar_se"
preenchidos; o critério tem de ter a forma "o que roda → o que tem de sair". Sai 0 quando passa.
"""
import sys

import yaml

ORDEM = ["sim", "sim2sim", "suspenso", "chão"]
CAMPOS = ["onde", "criterio", "parar_se"]


def main():
    if len(sys.argv) < 2:
        print(__doc__.strip())
        return 2
    e = yaml.safe_load(open(sys.argv[1])) or {}
    degraus = e.get("degraus") or []
    erros = []
    nomes = [str(d.get("nome", "")).strip() for d in degraus]
    if nomes != ORDEM:
        erros.append(f"degraus {nomes or 'nenhum'}; o esperado é {ORDEM}, nesta ordem")
    criterios = 0
    for d in degraus:
        n = d.get("nome", "?")
        vazios = [c for c in CAMPOS if not str(d.get(c) or "").strip()]
        if vazios:
            erros.append(f"degrau '{n}' sem {', '.join(vazios)}")
        crit = str(d.get("criterio") or "")
        if crit and "→" not in crit and "->" not in crit:
            erros.append(f"degrau '{n}': o critério precisa de 'comando → saída esperada'")
        elif crit:
            criterios += 1
    for c in ("politica", "robo"):
        if not str(e.get(c) or "").strip():
            erros.append(f"falta '{c}'")
    for x in erros:
        print(f"ERRO: {x}")
    print(f"{len(degraus)} degraus, {criterios} critérios" + (" · escada ok" if not erros else f" · {len(erros)} problema(s)"))
    return 1 if erros else 0


if __name__ == "__main__":
    raise SystemExit(main())
