F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
python3 kit/portao_sim2sim.py --passo 0.001 --dds 2>/dev/null; echo "saída: $?"
