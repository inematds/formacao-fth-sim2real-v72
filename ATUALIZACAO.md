# ATUALIZACAO — FTH 2 · Do simulador ao chão (19/10/2026)

Conferência "atualizar, não copiar": cada afirmação das fontes antigas usadas neste curso foi comparada com as pesquisas da formação (`~/projetos/wifi/longrun/2026-10-19-formacao-fth-v72/PESQUISA-ESTADO-DA-ARTE.md` = **PE**, `../2026-10-19-vla-v72/PESQUISA-ECOSSISTEMA.md` = **VE**) e com o que roda nesta máquina (aarch64, NVIDIA GB10, Python 3.12.3) em 19/10/2026 (= **medido**, com arquivo em `kit/saidas/`).
Fontes antigas (intocadas): FTH `26fe21c` (`niveis/nivel-4/modulo-2.md`, "Sim-to-Real Transfer", 29/10/2025) e robotica-real2sim `3a08537` (`README.md`, `docs/HUMANOIDES.md`, conferido pelo próprio projeto em 14/10/2026).
Legenda da coluna "curso diz agora": **fato** (fonte primária ou medido), **relatado** (fonte secundária, dito como tal no texto), **fora** (não entra por falta de fonte ou por ter dono em outro curso).

## O gap (aula 1)

| fonte antiga | o que dizia | o que o curso diz agora | fonte (URL/data) |
|---|---|---|---|
| FTH 4.2 §1.1 | "Taxa de sucesso: 95% no sim, 20% no real" (exemplo sem fonte) | **fora** como número. No lugar, uma medida reproduzível: a mesma política (unitree_rl_lab, G1 29 GDL) anda 4,7 m em 10 s no "sim" e cai em 2,2 s no "real simulado" (MuJoCo com parâmetros escondidos, dito como tal) | medido, `kit/saidas/a1b-dois-mundos.txt` |
| FTH 4.2 §1.2 | sensor real com ruído, "às vezes retorna None", "latência de 20–50 ms" (sem fonte) | latência entra como parâmetro medido no kit (0–40 ms) e o efeito é medido; o número "20–50 ms" não entra como fato | medido, aula 4 |
| FTH 4.2 §1.3 | 3 abordagens: simulação ultrarrealista, randomização, híbrido com ajuste no real | camadas de 2026: randomização → identificação do atuador (sysid do MuJoCo 3.5+) → sim2sim como portão → ajuste de Kp/Kd por motor → delta action (ASAP) quando o gap persiste | PE §4 + Top 10 item 6 |
| FTH 4.2 (todo) | treina "no Isaac Sim" sem versão; `from omni.isaac.core import World` | política pronta treinada no **Isaac Lab** (unitree_rl_lab `4960b84`, 19/11/2025) e rodada no **MuJoCo 3.16.0**; Isaac Sim 6.1 / Isaac Lab 3.0 EA só como "o que se usa em escala", com link | https://github.com/unitreerobotics/unitree_rl_lab · VE §2 |
| — (ausente) | — | atuação, atraso, atrito e massa separados por experimento: nenhum parâmetro sozinho derruba a política; os quatro juntos derrubam | medido, `kit/saidas/a1c-um-por-vez.txt` |

## Domain randomization (aula 2)

| fonte antiga | o que dizia | o que o curso diz agora | fonte (URL/data) |
|---|---|---|---|
| FTH 4.2 §2.1 | faixas genéricas: gravidade 9,6–10,0, atrito 0,3–1,2, massa ±10 %, motor ±5 %, latência 10–30 ms | as faixas **reais** de uma política publicada: atrito 0,3–1,0, massa do tronco −1 a +3 kg, empurrão por velocidade ±0,5 m/s a cada 5 s, ruído de observação (sem kp/kd nem atraso randomizados) | `velocity_env_cfg.py`, classe `EventCfg`, unitree_rl_lab `4960b84` |
| FTH 4.2 §2.1 | "gravidade varia por altitude" como item a randomizar | **fora** (a política real não randomiza gravidade; o efeito na Terra é desprezível para locomoção) | idem |
| FTH 4.2 §2.2 | código `omni.isaac.core` com `np.random` por episódio | randomização é configuração de eventos (`EventTerm`, modo startup/reset/interval) no Isaac Lab "manager-based"; o mjlab usa a mesma API sobre MuJoCo Warp | unitree_rl_lab · https://github.com/mujocolab/mjlab (PE §3.4) |
| FTH 4.2 §2.3 | 3 fases: sem randomização → leve → agressiva | mantém a ideia, mas a prática mede a **cobertura**: 20/20 dentro da faixa treinada × 8/20 fora dela (atrito 0,2–0,6, carga 2–8 kg, kp 0,6–1,0, atraso 0–30 ms) | medido, `kit/saidas/a2a-randomizar.txt` |
| FTH 4.2 (ref.) | IsaacGymEnvs como "domain randomization no Isaac Sim" | Isaac Gym é **legado** (a maioria dos repos novos migrou para Isaac Lab ou mjlab; PE §3.4 marca a síntese como incerta) e não é citado como caminho | PE §3.1, §3.4 |

## Identificação de sistema (aula 3)

| fonte antiga | o que dizia | o que o curso diz agora | fonte (URL/data) |
|---|---|---|---|
| FTH 4.2 §3.1 | tabela de parâmetros nominal × real (massa 8,0 × 8,3 kg, latência 5 × 18 ms, constante do motor 0,05 × 0,048 N·m/A) sem robô nem fonte | **fora** como números. O curso mede: ensaio de bancada no robô pendurado (varredura 0,5 → 3 Hz) e ajuste de kp e atraso | medido, `kit/saidas/a3*.txt` |
| FTH 4.2 §3.2 | `scipy.optimize` / `curve_fit` à mão | **toolbox `mujoco.sysid`** (MuJoCo 3.5.0, 12/02/2026; aqui 3.16.0 com `pip install "mujoco[sysid]"`): `Parameter` + `ModelSequences` + `optimize` | MuJoCo changelog 3.5.0 (VE §2; PE §4) |
| FTH 4.2 §3.2 | "modelo residual" `next_state = simulate_step + model(state, action)` | vira a aula 5 (delta action, ASAP, RSS 2025), com o nome certo e o repositório | https://github.com/LeCAR-Lab/ASAP (PE §3.2, §4) |
| — (ausente) | — | atraso de atuador nativo (`delay`, `nsample`, histórico em `mjData.history`) do MuJoCo 3.5+ | VE §2; medido no 3.16.0 |
| — (ausente) | — | BAM (Rhoban) e `mujoco-sysid` (PyPI) só citados como alternativas **relatadas** | PE §4 [2ª] |

## Atuador e atraso (aula 4)

| fonte antiga | o que dizia | o que o curso diz agora | fonte (URL/data) |
|---|---|---|---|
| FTH 4.2 §6.2 | medir latência com `time.time()` em volta de `set_joint_effort`; "> 50 ms é problema de rede" | atraso modelado no simulador e medido o efeito: com empurrão, 0 ms fica de pé e 20 ms já cai (tabela da aula); o limiar "50 ms" não entra | medido, `kit/saidas/a4a-atraso.txt` |
| — (ausente) | — | ajuste de Kp/Kd por motor no deploy como parte do sim-to-real: SONIC adicionou escalonamento por motor contra tropeço em 31/08/2026 | https://github.com/NVlabs/GR00T-WholeBodyControl (PE §3.2, §4) |
| — (ausente) | — | "actuator network" (rede que aprende o atuador) só como conceito, sem número | PE §4 (modelo de atuador) |

## Corrigir com dados do robô (aula 5)

| fonte antiga | o que dizia | o que o curso diz agora | fonte (URL/data) |
|---|---|---|---|
| FTH 4.2 §4.1 | "ajustes finais no robô real melhoram 10–30 %" | **fora** (sem fonte) | — |
| FTH 4.2 §3.2 | residual aprendido genérico | **ASAP** (CMU/NVIDIA, RSS 2025): pré-treino em sim → coleta no real → modelo de delta action → ajuste fino; o arquivo de movimento precisa da chave `"action"`. No kit: um **brinquedo linear** da ideia (mínimos quadrados), dito como tal | https://github.com/LeCAR-Lab/ASAP (PE §3.2, §4) |
| FTH 4.2 §4.3 | escalar ação a 30 % / 60 % / 100 % nos primeiros episódios | entra como conceito na escada (aula 8); procedimento de operação é dono do curso 4 | CURRICULO (dono de cada assunto) |

## Sim2sim (aula 6)

| fonte antiga | o que dizia | o que o curso diz agora | fonte (URL/data) |
|---|---|---|---|
| FTH 4.2 (ausente) | sem sim2sim | **sim2sim como portão** é o fluxo oficial do unitree_rl_lab (Isaac Lab → `unitree_mujoco`) e do Berkeley Humanoid Lite | PE §1.3, §4 |
| FTH 4.2 §5.2 | Dockerfile com "ROS 2 Humble + CUDA" como deploy | **fora** daqui: ROS 2 e contêiner por robô são do curso 4 (operar). Aqui o caminho é o do fabricante: `unitree_sdk2_python` + CycloneDDS 0.10.2 + `unitree_mujoco`, testado nesta máquina | PE §5; medido, `kit/saidas/a6*.txt` |
| real2sim docs/HUMANOIDES.md §4 | estudo de 2026 com o G1 em 8 ações da construção, avaliadas em dois motores de física antes do robô; só as que passaram foram ao G1 físico | entra como exemplo de portão, **segundo o robotica-real2sim (conferido em 14/10/2026)**, arXiv 2608.01600 | https://arxiv.org/pdf/2608.01600 |
| — (ausente) | — | erro de ordem das juntas (Isaac Lab × SDK, `joint_ids_map`) como falha número 1 de sim2sim, com captura real | medido, `kit/saidas/e6-ordem-errada.txt` |

## Real-to-sim (aula 7)

| fonte antiga | o que dizia | o que o curso diz agora | fonte (URL/data) |
|---|---|---|---|
| real2sim README | foto → cena → gêmeo MuJoCo com o Franka Panda; MuJoCo 3.15; medido em 14/10/2026 | roda o passo **sem modelo** (`r2s.py ver`, cena de exemplo) no venv do curso com MuJoCo 3.16.0; foto → cena (que chama modelo de visão) só mostrado; dono do assunto é o robotica-real2sim (link) | https://inematds.github.io/robotica-real2sim/guia/ · medido |
| real2sim HUMANOIDES.md §1 | GR00T N1 +40 % com dados sintéticos, 780 mil trajetórias em 11 h (NVIDIA, 03/2025) | **fora** (é VLA/dados: dono vla-v72); no máximo link | — |
| real2sim HUMANOIDES.md §3 | "1.620×" no treino do G1 no Isaac Lab, 4.096 ambientes | **fora** como número (o próprio doc diz que é conta derivada e muda com a versão); locomoção em GPU é do curso 1 | — |
| — (ausente) | — | Gaussian splatting para humanoide: Niantic Spatial + Flexion + NVIDIA e GaussGym — **relatado**, demo de fornecedor, sem sim-to-real medido em paper | PE §4 [2ª] |

## Escada (aula 8)

| fonte antiga | o que dizia | o que o curso diz agora | fonte (URL/data) |
|---|---|---|---|
| FTH 4.2 §4.3 | níveis 0–4 (sim limpa → leve → agressiva → parâmetros identificados → robô real) | escada de 4 degraus com critério de passagem cada: sim (com randomização) → sim2sim (outro motor/modelo + caminho de mensagens do robô) → suspenso (pórtico/elástico) → chão; o fluxo do unitree_rl_lab usa elástico/suspensão antes de soltar o robô | PE §6.1 [FATO] |
| FTH 4.2 §4.2 | checklist (3×3 m, colchões, e-stop < 2 m, torque 50 %, watchdog 100 ms, óculos) | **fora** como procedimento (dono: curso 4, aula 1); aqui só a menção de que a escada exige critério de parada | CURRICULO |
| FTH 4.2 §5.3–5.4 | Prometheus/Grafana, OTA | **fora** (operação: curso 4) | — |
| FTH 4.2 (geral) | "Live semanal", fórum, `discord.gg/fth-nivel4` | **fora** (link inventado; INEMA é aberto e gratuito) | AUDITORIA |
| FTH 4.2 (refs.) | papers 2017–2022 (OpenAI dynamics randomization; Google quadruped 2018; NVIDIA "Learning to Walk in Minutes", 2022) | este último fica como referência histórica do PPO paralelo (é o paper do legged_gym, legado); os vídeos de terceiros ("Lex Fridman", "Two Minute Papers") **saem** | AUDITORIA; regra "não citar curso/vídeo de terceiros" |

## Ficou de fora por falta de fonte
- Números de ganho de "fine-tuning no real" (10–30 %), taxas "95 % → 20 %" e qualquer latência típica de robô comercial.
- Faixas de randomização de kp/kd e atraso "recomendadas": a política usada não as randomiza; o curso mostra o efeito, não recomenda número.
- Versão atual do `unitree_sdk2` (PE: [incerto]) → o curso fixa o commit testado (`unitree_sdk2_python 814556d`, 21/09/2026).
