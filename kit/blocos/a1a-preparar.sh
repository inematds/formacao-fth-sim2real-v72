F=${FTH:-$HOME/fth}; mkdir -p $F && cd $F
[ -d .venv ] || python3.12 -m venv .venv
. .venv/bin/activate && pip install -q mujoco==3.16.0 numpy onnxruntime==1.31.0 pyyaml
[ -d sim2real ] || git clone -q --depth 1 https://github.com/inematds/formacao-fth-sim2real-v72 sim2real
[ -d mujoco_menagerie ] || git clone -q --filter=blob:none --sparse https://github.com/google-deepmind/mujoco_menagerie
git -C mujoco_menagerie sparse-checkout add unitree_g1 && git -C mujoco_menagerie checkout -q 62ab00f
[ -d unitree_rl_lab ] || git clone -q --filter=blob:none --sparse https://github.com/unitreerobotics/unitree_rl_lab
git -C unitree_rl_lab sparse-checkout set deploy/robots/g1_29dof/config/policy/velocity
git -C unitree_rl_lab checkout -q 4960b84 && git -C unitree_rl_lab log -1 --format='unitree_rl_lab %h (%ad)' --date=short
python3 -c "import mujoco, onnxruntime; print('mujoco', mujoco.__version__, '· onnxruntime', onnxruntime.__version__)"
