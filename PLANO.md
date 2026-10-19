# PLANO — FTH 2 · Do simulador ao chão (formacao-fth-sim2real-v72)

Curso 2 de 5 da **FTH — Formação Tecnológica em Humanoides** (v7.2, PT/EN/ES). Público: quem programa em Python, já viu ROS 2 e quer levar uma política de humanoide para o robô, sem ter um. Toda prática roda em CPU; o "robô real" é um MuJoCo com parâmetros escondidos (`kit/mundos/real.json`), dito como tal.
Fronteira: o `vla-v72` aula 6 dá o conceito de reality gap e a avaliação em sim; aqui é **como fechar o gap num humanoide com pernas**. Curso anterior: `formacao-fth-locomocao-v72` (treino por RL). Próximo: `formacao-fth-corpo-inteiro-v72`.

## Versões testadas nesta máquina (19/10/2026, aarch64 / NVIDIA GB10, Ubuntu, Python 3.12.3)
| item | versão | como |
|---|---|---|
| MuJoCo | **3.16.0** (wheel aarch64 do PyPI) | `pip install mujoco==3.16.0` (venv do curso 0 reaproveitado) |
| mujoco.sysid | 3.16.0 (extra) | `pip install "mujoco[sysid]==3.16.0"` (scipy, matplotlib, plotly…) — sem o extra, `sysid.optimize` não existe |
| onnxruntime | **1.31.0** (wheel aarch64) | `pip install onnxruntime==1.31.0` |
| numpy / pyyaml | 2.5.4 / atual | idem |
| MuJoCo Menagerie | commit **62ab00f** (15/10/2026) | `sparse-checkout add unitree_g1` (+ `franka_emika_panda` na aula 7) |
| Política | **unitree_rl_lab 4960b84** (19/11/2025), `deploy/robots/g1_29dof/config/policy/velocity/v0` (policy.onnx 480 → 29, deploy.yaml) | `git clone --filter=blob:none --sparse` + `sparse-checkout set …/velocity` |
| CycloneDDS (C) | `releases/0.10.x` **5041f35** (22/03/2026), compilado com cmake | `pip install cyclonedds==0.10.2` falha sem a lib C em aarch64; fallback compila (1–2 min) e exporta `CYCLONEDDS_HOME` |
| cyclonedds (Python) | 0.10.2 | pip, contra o C acima |
| unitree_sdk2_python | **814556d** (21/09/2026) + pygame | `pip install -e` |
| unitree_mujoco | **1eb6642** (07/09/2026) | clone; ponte `simulate_python/unitree_sdk2py_bridge.py` |
| robotica-real2sim | **3a08537** (15/10/2026) | clone; `vendor/menagerie` → link para o Menagerie da bancada |

Armadilhas achadas no teste (viraram conteúdo):
- A tag `0.10.2` do CycloneDDS C abortou com `*** buffer overflow detected ***` ao criar o domínio (glibc com FORTIFY); a branch `releases/0.10.x` (5041f35) funciona. O cache do pip pode esconder isso (wheel de outra máquina): teste com `PIP_NO_CACHE_DIR=1`.
- A interface `lo` não faz multicast: dois processos DDS não se descobrem. O kit acrescenta `Discovery/Peers 127.0.0.1` à configuração da Unitree só quando a interface é `lo` (`s2r.iniciar_dds`).
- A ponte do `unitree_mujoco` importa `pygame` mesmo sem joystick.
- `deploy.yaml`: `stiffness`/`damping` vêm na ordem do robô (SDK); `default_joint_pos` e as ações, na ordem do Isaac Lab (`joint_ids_map`). Trocar isso derruba o robô em 1 s (aula 6, erro comum).
- `unitree_mujoco` com passo de 5 ms e integrador de Euler: o PD dos punhos (5 N·m, kd 10) oscila e fica no limite de torque; com 1–2 ms some.
- `mujoco.sysid`: sensores do modelo têm de ser exatamente os do log (a IMU do Menagerie sai da bancada); controle entra por `TimeSeries.from_control_names`.
- Atuador com `delay` começa com o histórico zerado: o kit enche com `mj_initCtrlHistory` (sem isso, os primeiros 20 ms mandam alvo 0).

Determinismo: aulas 1–5, 7 e 8 rodadas duas vezes seguidas com `kit/capturar.sh` → `diff -r` sem diferença (ver fim). A etapa 3 do portão (DDS em tempo real) varia de uma rodada para outra: o "pronto quando" dela é estrutural (`PORTÃO: passou (3 de 3 etapas)`).
**Mostrado, não testado aqui:** mjlab, MuJoCo Playground, Isaac Lab 3.0 EA / Isaac Sim 6.1 (GPU, ambientes próprios), ASAP completo (Isaac Gym/Isaac Lab + RL), unitree_ros2 (Humble; curso 4). Foto → cena do real2sim chama modelo de visão: só citado.

## Pasta do aluno
`~/fth/` (variável `FTH`) do curso 0: `.venv/`, `mujoco_menagerie/` e, deste curso, `sim2real/` (clone deste repo), `unitree_rl_lab/`, `log.npz`, e na aula 6 `cyclonedds/`, `unitree_sdk2_python/`, `unitree_mujoco/`; na aula 7 `robotica-real2sim/`. Os blocos começam com `F=${FTH:-$HOME/fth}`; a captura roda o mesmo texto com `FTH=<scratchpad>` e troca o caminho por `~/fth`.

## Aulas (objetivo · diagrama · prática "pronto quando", já testada)
| # | slug | objetivo (≤ 160) | diagrama | pronto quando (comando → saída) |
|---|---|---|---|---|
| 1 | gap | medir o gap rodando a mesma política em "sim" e "real simulado" e achar que nenhum parâmetro sozinho a derruba | atuador, atraso, atrito, massa, contato → queda | `python3 kit/dois_mundos.py; echo "saída: $?"` → `real simulado … queda: sim em t = 2.3 s` + `saída: 1`; `--so kp` → `queda: não` (vel. 0.75) |
| 2 | randomizacao | ler as faixas de randomização de um treino real e medir a sobrevivência dentro e fora delas | treino (faixas) → política → mundos sorteados → sobreviveu X/20 | `python3 kit/randomizar.py --seeds 20` → `faixa treino  sobreviveu: 20/20` e `faixa fora    sobreviveu: 8/20` |
| 3 | sysid | identificar o kp e o kd do atuador num ensaio de bancada com o toolbox mujoco.sysid | pórtico → varredura → log → modelo → otimizador → parâmetro | `python3 kit/sysid.py ~/fth/log.npz --revelar; echo "saída: $?"` → linha do kp `dentro de ±10 %: sim` (escondido 0.60) + `saída: 0` |
| 4 | atuador | medir o atraso do atuador na bancada e ver quantas quedas ele causa sob empurrão | política 50 Hz → rede/atraso → PD 500 Hz–1 kHz → motor (limite) | `python3 kit/atraso.py --ms 0 20 40` → `0 ms 2/6`, `20 ms 3/6`, `40 ms 6/6`; `--medir` → `atraso medido (real − sim): 22 ms` |
| 5 | corrigir | corrigir o simulador com dados do robô por uma ação delta e medir o erro de rastreio antes e depois | pré-treino → coleta → modelo delta → sim corrigido → ajuste | `python3 kit/delta.py ~/fth/log.npz; echo "saída: $?"` → `erro de rastreio sim × real: antes 8.16° → depois N°` (N < 8,16) + `saída: 0` |
| 6 | sim2sim | passar a política por um portão de três etapas: outro modelo do robô e o caminho DDS de mensagens | Menagerie → unitree_mujoco → DDS (rt/lowcmd, rt/lowstate) → portão | `python3 kit/portao_sim2sim.py --passo 0.001 --dds; echo "saída: $?"` → `PORTÃO: passou (3 de 3 etapas)` + `saída: 0` |
| 7 | real2sim | rodar o gêmeo do robotica-real2sim no venv do curso e provar o plano na física antes do robô | foto → cena.json → gêmeo MuJoCo → episódios → prova | `python3 kit/gemeo.py …` → `objetos na cena: 4` e `gemeo.png: 1280×720 px` ; `r2s.py provar … -n 20` → `APROVADO para o robô real` |
| 8 | escada | escrever a escada sim → sim2sim → suspenso → chão com critério de passagem e de parada em cada degrau | escada de 4 degraus + simfila + mapa + gerador | `python3 kit/conferir_escada.py ~/fth/escada.yaml; echo "saída: $?"` → `4 degraus, 4 critérios · escada ok` + `saída: 0` |

Saídas de erro comum capturadas: `e1-sem-politica` (1), `e3-so-kp` (3: só kp, o atraso vaza para ele), `e6-ordem-errada` (6), `e7-sem-gpu` (7, `MUJOCO_GL=osmesa` sem a lib), `e8-escada-incompleta` (8). Na 2 e na 4 o "erro comum" é uma leitura errada de saída real (`fora` detalhado; 0 ms também cai com empurrão lateral).

## Simulação de ciclo
`simfila` na aula 8: os 4 degraus da escada como fila (sim → sim2sim → suspenso → chão), com a falha proposital no degrau "suspenso" na primeira vez e a volta ao degrau anterior.

## Links fixos
- Curso anterior: https://inematds.github.io/formacao-fth-locomocao-v72/ (em construção em paralelo em 19/10/2026 — 404 esperado no `validar --links`).
- Curso seguinte (aula 8, `links`): https://inematds.github.io/formacao-fth-corpo-inteiro-v72/ (ainda não publicado — 404 esperado).
- Donos externos: vla-v72 aula 6 (avaliação em sim, reality gap), aula 8 (normas); robotica-real2sim (real-to-sim com braço); curso 4 da FTH (operar: SDK, ROS 2, segurança).

Determinismo conferido em 19/10/2026: duas capturas completas seguidas (`kit/capturar.sh`, 25 blocos) → `diff -r` com uma única diferença, a etapa 3 do portão (DDS em tempo real: "andou 5.2 m" × "5.3 m"), já declarada como variável.
