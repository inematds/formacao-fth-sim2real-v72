F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
python3 kit/randomizar.py --seeds 20 --faixa fora --detalhe | head -6
