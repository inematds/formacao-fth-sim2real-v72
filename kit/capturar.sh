#!/usr/bin/env bash
# capturar.sh — roda cada bloco "Terminal" do curso (kit/blocos/*.sh) e grava a saída em kit/saidas/.
# É daqui que saem as abas "Saída capturada" das aulas.
# Uso: FTH=<pasta de ensaio> bash kit/capturar.sh [bloco...]
#   A pasta de ensaio faz o papel de ~/fth: recebe .venv, mujoco_menagerie, unitree_rl_lab… e o link "sim2real"
#   para este repo. O caminho da pasta de ensaio é trocado por ~/fth nas saídas, para a aba mostrar o que o
#   aluno vê. Teto por bloco: timeout ${CAPTURA_TIMEOUT:-900} s e MemoryMax=${CAPTURA_MEM:-8G}.
set -uo pipefail
K=$(cd "$(dirname "$0")" && pwd)
: "${FTH:?defina FTH=<pasta de ensaio>}"
mkdir -p "$FTH" "$K/saidas"
[ -e "$FTH/sim2real" ] || ln -s "$(dirname "$K")" "$FTH/sim2real"
teto=(); command -v systemd-run >/dev/null && teto=(systemd-run --user --scope -q -p "MemoryMax=${CAPTURA_MEM:-8G}")
alvos=("$@"); [ ${#alvos[@]} -eq 0 ] && alvos=($(cd "$K/blocos" && ls *.sh | sed 's/\.sh$//'))
for b in "${alvos[@]}"; do
  ( cd /tmp && FTH="$FTH" timeout "${CAPTURA_TIMEOUT:-900}" "${teto[@]}" bash "$K/blocos/$b.sh" ) 2>&1 \
    | sed "s#$FTH#~/fth#g" > "$K/saidas/$b.txt"
  echo "$b: $(wc -l < "$K/saidas/$b.txt") linhas"
done
