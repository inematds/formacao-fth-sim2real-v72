F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
[ -f $F/escada.yaml ] || cp kit/escada-modelo.yaml $F/escada.yaml
python3 kit/conferir_escada.py $F/escada.yaml; echo "saída: $?"
