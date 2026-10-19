F=${FTH:-$HOME/fth}; cd $F/sim2real && . $F/.venv/bin/activate
cat > $F/so-kp.json <<'J'
{"nome": "so-kp", "atrito": [0.3, 1.0], "massa": [-1.0, 3.0], "kp": [0.5, 0.8], "empurrao_vel": [-0.5, 0.5]}
J
python3 kit/randomizar.py --seeds 20 --faixa $F/so-kp.json
