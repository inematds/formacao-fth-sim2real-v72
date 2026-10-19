F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
for p in atrito massa kp atraso_ms; do python3 kit/dois_mundos.py --so $p | tail -1; done
