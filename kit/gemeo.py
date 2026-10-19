#!/usr/bin/env python3
"""gemeo.py — confere o gêmeo do robotica-real2sim: quantos objetos a cena tem e se a imagem saiu.

Uso: python3 kit/gemeo.py <cena.json> <gemeo.png>
"""
import json
import struct
import sys
from pathlib import Path


def main():
    if len(sys.argv) < 3:
        print(__doc__.strip())
        return 2
    cena, img = Path(sys.argv[1]), Path(sys.argv[2])
    c = json.load(open(cena))
    objs = c.get("objetos", [])
    print(f"cena: {cena.name} · mesa {c['mesa'].get('largura', '?')} × {c['mesa'].get('profundidade', '?')} m · objetos na cena: {len(objs)}")
    for o in objs:
        print(f"  {o.get('nome', '?'):<16} {o.get('forma', o.get('tipo', '?'))}")
    if not img.exists():
        print(f"ERRO: {img} não existe")
        return 1
    with open(img, "rb") as f:
        cab = f.read(24)
    w, h = struct.unpack(">II", cab[16:24])
    print(f"{img.name}: {w}×{h} px, {img.stat().st_size // 1024} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
