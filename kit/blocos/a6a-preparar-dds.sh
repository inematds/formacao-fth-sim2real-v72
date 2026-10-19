F=${FTH:-$HOME/fth}; cd $F && . .venv/bin/activate
pip install -q cyclonedds==0.10.2 2>/dev/null || {
  [ -d cyclonedds ] || git clone -q --filter=blob:none -b releases/0.10.x https://github.com/eclipse-cyclonedds/cyclonedds
  git -C cyclonedds checkout -q 5041f35
  cmake -S cyclonedds -B cyclonedds/build -DCMAKE_INSTALL_PREFIX=$F/cyclonedds/install -DBUILD_EXAMPLES=OFF > /dev/null
  cmake --build cyclonedds/build --target install -j 4 > /dev/null 2>&1
  export CYCLONEDDS_HOME=$F/cyclonedds/install && pip install -q cyclonedds==0.10.2; }
git -C cyclonedds log -1 --format="cyclonedds (C) %H (%ad)" --date=short 2>/dev/null | sed -E 's/([0-9a-f]{7})[0-9a-f]{33}/\1/'
[ -d unitree_sdk2_python ] || git clone -q https://github.com/unitreerobotics/unitree_sdk2_python
git -C unitree_sdk2_python checkout -q 814556d && pip install -q -e unitree_sdk2_python pygame
[ -d unitree_mujoco ] || git clone -q https://github.com/unitreerobotics/unitree_mujoco
git -C unitree_mujoco checkout -q 1eb6642 && git -C unitree_mujoco log -1 --format='unitree_mujoco %h (%ad)' --date=short
python3 -c "import importlib.metadata as m, unitree_sdk2py; print('cyclonedds', m.version('cyclonedds'), '· unitree_sdk2py ok')"
