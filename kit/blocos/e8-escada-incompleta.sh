F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
grep -v "parar_se: tropeço" kit/escada-modelo.yaml > $F/escada-incompleta.yaml
python3 kit/conferir_escada.py $F/escada-incompleta.yaml; echo "saída: $?"
