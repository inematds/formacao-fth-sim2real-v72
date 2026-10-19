F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
python3 kit/coletar.py --mundo sim --saida $F/log-sim.npz | tail -1
python3 kit/sysid.py $F/log-sim.npz | tail -4
