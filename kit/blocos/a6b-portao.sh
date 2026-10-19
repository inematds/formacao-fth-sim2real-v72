F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
python3 kit/portao_sim2sim.py; echo "saída: $?"
