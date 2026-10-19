F=${FTH:-$HOME/fth}; cd $F && . .venv/bin/activate && pip install -q pillow imageio
git -C mujoco_menagerie sparse-checkout add franka_emika_panda
[ -d robotica-real2sim ] || git clone -q https://github.com/inematds/robotica-real2sim
git -C robotica-real2sim checkout -q 3a08537 && mkdir -p robotica-real2sim/vendor
ln -sfn $F/mujoco_menagerie robotica-real2sim/vendor/menagerie
cd robotica-real2sim && python3 r2s.py ver exemplos/mesa-foto/cena.json $F/gemeo.png --camera cima
python3 $F/sim2real/kit/gemeo.py exemplos/mesa-foto/cena.json $F/gemeo.png
