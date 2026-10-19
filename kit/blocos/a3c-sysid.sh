F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
python3 kit/sysid.py $F/log.npz --revelar; echo "saída: $?"
