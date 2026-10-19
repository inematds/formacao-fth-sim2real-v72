Nota: 8.5/10

Revisor independente (não o autor) · 19/10/2026 · curso PT inteiro (curso.json + 8 aulas), conferido contra PESQUISA-ESTADO-DA-ARTE.md, PESQUISA-ECOSSISTEMA.md, PESQUISA-MODELOS.md, `kit/saidas/*.txt`, código do `kit/`, clone do unitree_rl_lab `4960b84`, Menagerie `62ab00f`, unitree_mujoco `1eb6642` e unitree_sdk2_python do scratchpad. Nenhum treino nem script pesado foi rodado.

## Resumo em 3 linhas
1. Curso sólido e honesto: o "real simulado" é sempre dito como ensaio, cada número de prática vem de saída capturada, as abas "Saída capturada" batem linha a linha com `kit/saidas/` e os fatos do campo vêm das pesquisas com data.
2. Um problema GRAVE: na aula 2 há um número sem fonte (atrito 0,3/0,2 e "caía em 1,9 s"), atribuído à aula 1, onde ele não aparece.
3. O resto são problemas menores: alguns "pronto quando" que não batem literalmente por causa dos espaços, uma leitura errada da saída (a "maior massa"), uma contradição sobre o atraso entre as aulas 1 e 2, uma meia-verdade sobre o torque do punho e uma afirmação [2ª] escrita como fato no resumo da aula 7.

## 15 fatos sorteados

| # | Fato | Onde | Fonte | Resultado |
|---|---|---|---|---|
| 1 | MuJoCo 3.16.0 é a versão atual | curso.json `lado_card.texto`; aula 1, bloco de preparação | PESQUISA-ECOSSISTEMA l.31 (3.16.0, 14/10/2026, [FATO]); a1a-preparar.txt | ok |
| 2 | `mujoco.sysid` chegou no MuJoCo 3.5.0 (12/02/2026) | 03-sysid `secoes[1].sub` | PESQUISA-ESTADO-DA-ARTE l.18 e l.158 [FATO] | ok |
| 3 | Atrito estático e dinâmico entre 0,3 e 1,0 em todos os corpos, no startup | 02-randomizacao `passos[0]` | `velocity_env_cfg.py` l.92–101 (`body_names=".*"`, `mode="startup"`) | ok |
| 4 | Massa de −1 a +3 kg somada ao `torso_link` | 02-randomizacao `passos[1]` | `velocity_env_cfg.py` l.104–111 (`operation: add`) | ok |
| 5 | `push_robot` a cada 5 s, ±0,5 m/s em x e y; sem randomização de kp, kd nem atraso | 02-randomizacao `passos[2]`, `passos[3]` | `velocity_env_cfg.py` l.151–156; a EventCfg não tem termo de ganho nem de atraso | ok |
| 6 | A política recebe 480 números (5 instantes) e decide a 50 Hz | 01-gap `passos[0].texto[1]`; 04-atuador nó Política | `deploy.yaml`: `step_dt: 0.02`, `history_length: 5`; 5 × (3+3+3+29+29+29) = 480 | ok |
| 7 | unitree_rl_lab `4960b84` (19/11/2025), Apache-2.0 | curso.json; 01-gap | `git log` do clone (2025-11-19); `LICENCE` = Apache 2.0 | ok |
| 8 | No MJCF do Menagerie: 139 N·m no joelho e 5 N·m no punho | 04-atuador `nos[3].detalhe` | `unitree_g1/g1.xml`: joelho ±139 ✓; punho pitch/yaw ±5, mas **roll ±25** | parcial (ver menores) |
| 9 | kd = 10 no punho | 06-sim2sim `passos[1].texto[0]` | `deploy.yaml` `damping`: braços (índices 15–28) = 10.0 | ok |
| 10 | unitree_mujoco vem com passo de 5 ms, integrador de Euler, domínio 1 | 06-sim2sim `passos[1]`, `nos[2].itens` | `simulate_python/config.py`: `SIMULATE_DT = 0.005`, `DOMAIN_ID = 1`; `g1_29dof.xml` sem `<option>` (Euler é o padrão) | ok |
| 11 | O SDK pede `cyclonedds==0.10.2` | 06-sim2sim `passos[3]` | `unitree_sdk2_python/setup.py` l.17 | ok |
| 12 | GR00T-WholeBodyControl acrescentou kp/kd por motor contra tropeço no SONIC em 31/08/2026 | 04-atuador `passos[3].texto[0]` | PESQUISA-ESTADO-DA-ARTE l.127 e l.161 [FATO] | ok |
| 13 | ASAP (RSS 2025): 4 etapas; arquivo de movimento com a chave "action"; modelo delta treinado como rede por RL | 05-corrigir lead, `nos[1]`, `nos[2]`, `passos[3]` | PESQUISA-ESTADO-DA-ARTE l.121 e l.160 [FATO]; o README do LeCAR-Lab/ASAP treina o delta com `exp`/`rewards` (pipeline de RL) | ok |
| 14 | GaussGym (Berkeley/ETH/Amazon FAR), 3DGS, 100 mil+ passos/s, arXiv 2510.15352 | 07-real2sim `passos[1]` | PESQUISA-ESTADO-DA-ARTE l.163 **[2ª]**; o subtítulo do passo diz "relatado" | ok (dito como relatado) |
| 15 | "Na aula 1, atrito 0,3 ainda andava e 0,2 caía em 1,9 s" | 02-randomizacao `passos[0].texto[1]` | não está em nenhuma saída do kit; a aula 1 não tem esse ensaio; `dois_mundos.py` só aceita `--so`, `--kp-comando` e `--vel`; o "1.9" de a1b é "andou 1.9 m" | **PROBLEMA (grave)** |

Conferidos também (fora da amostra): o fluxo oficial Isaac Lab → unitree_mujoco → robô (PESQUISA l.70/162 + README do unitree_rl_lab), a suspensão no deploy do unitree_rl_lab (PESQUISA l.190 [FATO]; o README mostra o elastic band no sim2sim), o Berkeley Humanoid Lite com sim2sim aberto (l.72 [FATO]), os critérios do portão no código (`TOL = 0.15`, 1 %, `hz < 45`), os 6 empurrões de 120/150/180 N por 0,2 s (`atraso.py` l.17), o ruído de 0,002 rad e 0,02 rad/s com varredura de 0,5 → 3 Hz (`coletar.py`, `s2r.py`), a semente 7 (`randomizar.py` l.36), `ModelSequences`/`TimeSeries.from_control_names`/`from_names` (`sysid.py` l.59–61) e `minimize.least_squares` (`delta.py` l.50). arXiv 2608.01600 está fora das três pesquisas, mas vem de fonte local conferida (`robotica-real2sim/docs/HUMANOIDES.md`) e aparece como "segundo o robotica-real2sim": está ok, com essa ressalva.

## Conferência dos "pronto quando" (24 exercícios)

| Aula · Ex. | Trecho citado | Saída | Resultado |
|---|---|---|---|
| 1 · E1 | `unitree_rl_lab 4960b84 (2025-11-19)`, `mujoco 3.16.0 · onnxruntime 1.31.0` | a1a | bate |
| 1 · E2 | `real simulado … queda: sim em t = 2.3 s`, `saída: 1` | a1b | bate (a elipse está dentro do code) |
| 1 · E3 | as 4 linhas "terminam em" `queda: não`; `vel. 0.75 m/s; pedida 0.50` | a1c | conteúdo bate, mas as linhas **contêm** `queda: não`, não terminam nele (menor) |
| 1 · E3 (texto) | — | — | escrita, sem saída |
| 2 · E1 | `faixa treino  sobreviveu: 20/20`, `faixa fora    sobreviveu: 8/20` | a2a | bate literalmente |
| 2 · E2 | `faixa so-kp   sobreviveu: 11/20` | a2c | bate literalmente |
| 2 · E3 | três linhas escritas | — | escrita; o exemplo "11/20" bate com a2c |
| 3 · E1 | `gravado: ~/fth/log.npz`, `enc_left_knee … 50.0°` | a3b | bate (elipse) |
| 3 · E2 | `kp escondido 0.60 · dentro de ±10 %: sim`, `saída: 0` | a3c | **não literal**: na saída é `kp         escondido   0.60 · …` (espaços colapsados; um `grep` do aluno falha) (menor) |
| 3 · E3 | `kp nominal 1.00 → identificado 1.00` | a3d | **não literal**, pelo mesmo motivo (menor) |
| 4 · E1 | `atraso medido (real − sim): 22 ms` | a4b | bate |
| 4 · E2 | `0 ms  2/6`, `20 ms  3/6`, `40 ms  6/6` | a4a | bate |
| 4 · E3 | `real simulado … queda: não`, `saída: 0` | a4c | bate |
| 5 · E1 | `erro de rastreio sim × real: antes 8.16° → depois 3.82°`, `saída: 0` | a5 | bate |
| 5 · E2 | a entre −0,48 e −0,71 | a5 | bate (−0.48 … −0.71) |
| 5 · E3 | escrita | — | escrita |
| 6 · E1 | `cyclonedds 0.10.2 · unitree_sdk2py ok` | a6a | bate |
| 6 · E2 | `PORTÃO: passou (3 de 3 etapas)`, `saída: 0` | a6c | bate (só a linha do PORTÃO, como combinado). O comando do pronto omite o `2>/dev/null` do bloco (menor) |
| 6 · E3 | `PORTÃO: reprovou — caiu em t = 1.0 s`, `saída: 1` | e6 | bate |
| 7 · E1 | `objetos na cena: 4`, `gemeo.png: 1280×720 px` | a7a | a saída bate, mas o **comando** `python3 kit/gemeo.py …` só funciona a partir de `sim2real/`; o bloco roda de `robotica-real2sim/` com `$F/sim2real/kit/gemeo.py` (menor) |
| 7 · E2 | `plano completo em 19/20 (95%); mínimo 90% -> APROVADO para o robô real` | a7b | bate |
| 7 · E3 | escrita | — | escrita |
| 8 · E1 | `4 degraus, 4 critérios · escada ok`, `saída: 0` | a8 | bate |
| 8 · E2/E3 | escrita / plano.md | — | escrita |

Todas as abas "Saída capturada" e "Erro comum" com `<pre>` conferem com os `.txt` correspondentes (incluindo e1, e3, e6, e7 e e8).

## Problemas GRAVES (impedem publicar)

1. **Número sem fonte e contradição entre aulas** — `conteudo/pt/aulas/02-randomizacao.json`, `secoes[1].passos[0].texto[1]`:
   > "Na aula 1, atrito 0,3 ainda andava e 0,2 caía em 1,9 s: o chão da faixa é o chão do que a política aguenta."

   A aula 1 não faz esse ensaio, nenhuma saída do kit tem esse valor e o aluno não consegue reproduzir (`dois_mundos.py` não fixa o atrito). Trocar por algo que as saídas sustentam, por exemplo:
   > "Fora da faixa (aula 2, detalhe), mundos com atrito de 0,20 a 0,30 caíram, sempre combinados com outros parâmetros: abaixo do chão da faixa, a política perde margem."

   Outra saída é apagar a frase. Se o ensaio existir, ele precisa virar bloco `codigo` com saída capturada em `kit/saidas/`.

## Melhorias menores

1. **Leitura errada da saída** — `02-randomizacao.json`, `secoes[3].saida.abas[1].html`: "O mundo 1 tem a maior massa e fica de pé". Nas 6 linhas, a maior massa é a do mundo 4 (7,93 kg), que cai. Trocar por "O mundo 1 tem massa de 7,38 kg e fica de pé; o 4, com 7,93 kg, cai".
2. **Contradição sobre o atraso (aulas 1 × 2)** — a aula 1 mostra que o atraso sozinho quase não muda nada (`só atraso_ms` → 0,46 m/s contra 0,47). Mesmo assim:
   - `02-randomizacao.json`, `passos[3].texto[0]`: "Exatamente os dois que a aula 1 mostrou que mudam o comportamento." → "O kp foi o que a aula 1 mostrou mudar o comportamento; o atraso pesa sob empurrão (aula 4)."
   - `02-randomizacao.json`, `perguntas[1].explica`: "Ganhos e atraso não estão, e foram eles que mudaram o comportamento na aula 1." → "Ganhos e atraso não estão: o kp mudou a marcha na aula 1 e o atraso derruba sob empurrão na aula 4."
3. **Torque do punho** — `04-atuador.json`, `secoes[0].nos[3].detalhe`: "5 N·m no punho" → "5 N·m no punho (pitch e yaw; o roll tem 25)". `06-sim2sim.json`, `passos[1].texto[0]`: "(limite de 5 N·m)" → "(5 N·m em pitch e yaw)".
4. **[2ª] escrito como fato** (a seção de passos e o quiz estão corretos, porque dizem "relatado"):
   - `07-real2sim.json`, `aprende[3].t`: "Real-to-sim para humanoide em 2026: ainda demo de fornecedor" → "Real-to-sim para humanoide em 2026: relatado como demo de fornecedor".
   - `07-real2sim.json`, `secoes[6].itens[2].texto`: "Gêmeo por splatting ainda é demo de fornecedor; medir o lugar já é rotina." → "Gêmeo por splatting: só demos de fornecedor relatadas até out/2026; medir o lugar já é rotina."
   - `07-real2sim.json`, `perguntas[1].opcoes[2]`: "Demo de fornecedor, sem sim-to-real medido em paper." → "Relatado como demo de fornecedor, sem medição publicada achada pela pesquisa."
5. **"Pronto quando" não literal (espaços)** — `03-sysid.json` E2: `kp escondido 0.60 · dentro de ±10 %: sim` → `dentro de ±10 %: sim` (trecho que aparece igual na saída) ou o texto com os espaços exatos. E3: `kp nominal 1.00 → identificado 1.00` → `→ identificado   1.00` com os 3 espaços, ou só `identificado   1.00`.
6. **Texto do pronto** — `01-gap.json`, `exercicios[2].pronto`: "as 4 linhas terminam em `queda: não`" → "as 4 linhas mostram `queda: não`".
7. **Comando do pronto no diretório errado** — `07-real2sim.json`, `exercicios[0].pronto`: `python3 kit/gemeo.py exemplos/mesa-foto/cena.json ~/fth/gemeo.png` → `python3 ~/fth/sim2real/kit/gemeo.py exemplos/mesa-foto/cena.json ~/fth/gemeo.png` (como no bloco, rodando de `robotica-real2sim/`).
8. **Pronto do portão diferente do bloco** — `06-sim2sim.json`, `exercicios[1].pronto`: acrescentar o `2>/dev/null` do bloco (`… --passo 0.001 --dds 2>/dev/null; echo "saída: $?"`) para o aluno ver as mesmas linhas.
9. **Semente e máquina** — `02-randomizacao.json`, `perguntas[3].opcoes[2]`: "Para o mesmo sorteio dar o mesmo placar em qualquer máquina." Tudo foi capturado em aarch64, e entre arquiteturas a física em ponto flutuante pode divergir. Trocar por "Para o mesmo sorteio se repetir e o placar ser comparável entre rodadas e políticas". Vale acrescentar ao curso uma nota única, por exemplo em `secoes[3].sub` da aula 2: "números capturados em aarch64; em x86_64 podem variar um pouco".
10. **Lead longo e generalização** — `04-atuador.json`, `lead`: 69 palavras (o teto é ~62). Cortar e trocar "É o mesmo ajuste de ganho por motor que projetos de 2026 fazem no deploy" (há uma fonte só, o SONIC) por "É o ajuste de ganho por motor que o SONIC, da NVIDIA, passou a fazer no deploy em 2026".
11. **Causa atribuída sem medida** — `02-randomizacao.json`, `secoes[3].saida.abas[1].html`: "(aqui, kp 0,60 com empurrão de 131 N)" afirma a causa da queda do mundo 6 sem ensaio isolado. Trocar por "(aqui, provavelmente o kp 0,60 somado ao empurrão)" ou tirar o parêntese.
12. **Fonte fora das pesquisas (ok, mas registrar)** — `06-sim2sim.json`, `secoes[0].legenda` (arXiv 2608.01600): a atribuição "segundo o robotica-real2sim, conferido em 14/10/2026" está correta, e o `ATUALIZACAO.md` (l.59) já traz a URL do arXiv. Não há o que mudar; fica só o registro de que a fonte está fora das três pesquisas.

## O que está bem (para não regredir)
- Honestidade sobre o ensaio: "real simulado" aparece entre aspas e "dito como tal", o `--revelar` vem com a ressalva de que no robô não existe valor escondido, e o delta.py é apresentado explicitamente como "não é o ASAP".
- Nenhum termo proibido (Webots, Isaac Gym como atual, Humble, Figure 01/02, K-Scale, "16 mil", ISO 25785, Thor, OpenVLA/Octo, MindOn, PREMIUM) e nenhum placeholder `<…>` fora de código.
- Os números da capa conferem: 125 min = soma das 8 aulas, 24 exercícios = 8 × 3, 3 etapas no portão.
- Os quizzes têm resposta certa e explicação coerentes com as saídas, com as exceções dos menores 2 e 9.

## Correções aplicadas pelo autor (19/10/2026)
- Grave (aula 2, atrito 0,3/0,2 sem fonte): frase trocada por fato da saída `a2b` (mundos 2 e 5, atrito ~0,2, caem).
- Menores 1–11: massa do mundo 1/4 corrigida e causa da queda deixada como hipótese; aula 1 × aula 2 alinhadas (kp muda a marcha; atraso pesa sob empurrão, aula 4); "5 N·m no pitch e no yaw do punho" (aulas 4 e 6); "demo de fornecedor (relatado)" na aula 7; "pronto quando" das aulas 1, 3, 6 e 7 reescritos para bater literalmente com as saídas (espaços, `2&gt;/dev/null`, caminho do gemeo.py); semente fixa "a cada rodada" (não "em qualquer máquina"); lead da aula 4 com 50 palavras e sem generalizar o SONIC.
