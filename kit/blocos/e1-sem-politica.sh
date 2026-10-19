F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
FTH=/tmp/sem-bancada python3 kit/dois_mundos.py; echo "saída: $?"
