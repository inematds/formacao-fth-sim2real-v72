F=${FTH:-$HOME/fth}; cd $F/robotica-real2sim && . $F/.venv/bin/activate
MUJOCO_GL=osmesa python3 r2s.py ver exemplos/mesa-foto/cena.json $F/gemeo.png --camera cima 2>&1 | tail -2
