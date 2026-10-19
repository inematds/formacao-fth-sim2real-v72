F=${FTH:-$HOME/fth}; cd $F && . .venv/bin/activate
pip install -q "mujoco[sysid]==3.16.0"
python3 -c "from mujoco import sysid; print('mujoco.sysid ok:', sysid.optimize.__name__, sysid.Parameter.__name__)"
