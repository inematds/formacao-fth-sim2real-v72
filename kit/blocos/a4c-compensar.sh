F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
python3 kit/dois_mundos.py --kp-comando 1.75; echo "saída: $?"
