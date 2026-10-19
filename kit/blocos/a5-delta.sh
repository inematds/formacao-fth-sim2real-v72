F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
python3 kit/delta.py $F/log.npz; echo "saída: $?"
