F=${FTH:-$HOME/fth}; cd $F/robotica-real2sim && . $F/.venv/bin/activate
python3 r2s.py provar exemplos/mesa-foto/cena.json resultados/mesa-foto/plano.json -n 20 | tail -3
