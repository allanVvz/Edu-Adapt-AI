# EduAdaptAI — Sistema de Prompts e Arquitetura de Desenvolvimento
## Projeto de Extensão PUCPR | Educação Inclusiva para Estudantes com TEA
### Base: Estudos Clínicos + Aplicação Real | Ensino Fundamental até 7º Ano

---

> **Fundamentação clínica:** DSM-5 (APA, 2013/2022), TEACCH (Schopler), ABA, PECS.  
> **Embasamento brasileiro:** CAED-UFSM (2023), REBENA v.9 (Pinto et al., 2024), Revista Eletrônica de Educação (Rossetto & Marcon, 2024), REASE v.10 (2024).

---

## PARTE 1 — PERFIS TEA (2 Perfis por Necessidade Clínica)

Os três níveis de suporte do DSM-5 foram condensados em **2 perfis pedagógicos funcionais** para aplicação até o 7º ano, priorizando a realidade escolar brasileira.

---

### 🟡 PERFIL A — "Leitor Silencioso"
**Baseado em: TEA Nível 1 de Suporte (DSM-5)**
*Evidência clínica: Pinto et al. (2024); UFSM-CAED (2023)*

**Quem é:**  
Estudante que comunica e interage, mas enfrenta dificuldades sociais e de interpretação contextual. Tende a mascarar sintomas. Alta funcionalidade em rotinas estruturadas. Pode ter hiperfoco em temas específicos. Leitura literal do mundo — dificuldade com metáforas, duplo sentido e linguagem figurada.

**Características mapeadas e confirmadas (→ atributos):**

| # | Característica Clínica | Atributo para Prompt |
|---|----------------------|---------------------|
| A1 | Leitura literal / dificuldade com duplo sentido | `linguagem_literal=true` |
| A2 | Hiperfoco em temas de interesse | `tema_ancora=variavel` |
| A3 | Dificuldade com transições e mudanças de contexto | `transicao_gradual=true` |
| A4 | Boa memória visual e sequencial | `suporte_visual=moderado` |
| A5 | Dificuldade com inferências sociais em texto | `inferencia_social=evitar` |
| A6 | Processamento mais lento em tarefas abertas | `abertura_resposta=estruturada` |
| A7 | Sensibilidade a sobrecarga de informação | `densidade_texto=baixa` |

---

### 🔴 PERFIL B — "Explorador Visual"
**Baseado em: TEA Nível 2 de Suporte (DSM-5)**
*Evidência clínica: Rossetto & Marcon (2024); REASE (2024)*

**Quem é:**  
Estudante com limitações mais visíveis na comunicação verbal e não verbal. Necessita de adaptação pedagógica estruturada e suporte visual robusto. Beneficia-se de rotinas fixas com antecipação visual. Comunicação alternativa pode estar presente (PECS, pictogramas). Dificuldade significativa com abstração e textos longos.

**Características mapeadas e confirmadas (→ atributos):**

| # | Característica Clínica | Atributo para Prompt |
|---|----------------------|---------------------|
| B1 | Comunicação verbal limitada ou em desenvolvimento | `modalidade_resposta=visual_ou_minima` |
| B2 | Necessidade de apoio visual constante | `suporte_visual=alto` |
| B3 | Dificuldade com texto corrido | `formato_texto=fragmentado` |
| B4 | Beneficia-se de rotina visual explícita | `sequencia_passos=sempre` |
| B5 | Interesse por repetição e previsibilidade | `estrutura_fixa=true` |
| B6 | Processamento sensorial atípico | `estimulos_extras=remover` |
| B7 | Dificuldade com múltiplos comandos simultâneos | `um_comando_por_vez=true` |
| B8 | Responde bem a reforço positivo imediato | `feedback_imediato=true` |

---

## PARTE 2 — SISTEMA DE ATRIBUTOS

Os atributos são variáveis que o usuário (professor/IA) preenche antes de gerar qualquer conteúdo. Eles **parametrizam todos os prompts** desta biblioteca.

```
ATRIBUTOS DO PERFIL [preencher antes de usar qualquer prompt]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
perfil              : [A | B]
nivel_suporte       : [1 | 2]
ano_escolar         : [1º ao 7º ano]
disciplina          : [Português | Matemática | Ciências | História | Geografia | Arte]
tema_ancora         : [tema de hiperfoco do aluno, ex: dinossauros, trens, planetas]
linguagem_literal   : [true | false]
suporte_visual      : [baixo | moderado | alto]
formato_texto       : [corrido | fragmentado | pictograma]
sequencia_passos    : [sempre | quando_necessario | nunca]
modalidade_resposta : [escrita | oral | visual | minima | arrastar_soltar | multipla_escolha]
densidade_texto     : [baixa | media | alta]
um_comando_por_vez  : [true | false]
feedback_imediato   : [true | false]
abertura_resposta   : [aberta | semi_estruturada | estruturada]
estimulos_extras    : [manter | reduzir | remover]
tema_imagem         : [concreto | abstrato | misto]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## PARTE 3 — BIBLIOTECA DE PROMPTS

---

### 📘 CATEGORIA 1: ESTRUTURAÇÃO E MELHORIA DE TEXTOS DE E-BOOK

---

#### PROMPT-EBOOK-01 | Reescrita de texto para Perfil A

```
Você é um especialista em educação inclusiva e design de conteúdo para estudantes com Transtorno do Espectro Autista (TEA) Nível 1 de Suporte.

ATRIBUTOS ATIVOS:
- perfil: A (Leitor Silencioso)
- linguagem_literal: true
- densidade_texto: baixa
- suporte_visual: moderado
- abertura_resposta: estruturada
- ano_escolar: {ano_escolar}
- disciplina: {disciplina}

TAREFA:
Reescreva o texto abaixo para que um estudante do {ano_escolar} com TEA Perfil A possa compreendê-lo com autonomia.

REGRAS OBRIGATÓRIAS:
1. Use linguagem direta, concreta e sem ambiguidade
2. Elimine completamente: metáforas, ironias, duplo sentido, expressões idiomáticas
3. Substitua frases longas por frases curtas (máximo 20 palavras por frase)
4. Use apenas um conceito por parágrafo
5. Adicione uma frase introdutória que diga EXATAMENTE o que o texto vai explicar
6. Use marcadores visuais (→, •) para indicar etapas ou listas
7. Finalize com uma frase de resumo no formato: "Resumindo: [conceito principal em 1 frase]"
8. Nível de vocabulário: acessível para {ano_escolar}

TEXTO ORIGINAL:
{inserir texto aqui}

TEXTO REESCRITO:
```

---

#### PROMPT-EBOOK-02 | Reescrita de texto para Perfil B

```
Você é um especialista em educação inclusiva com foco em Comunicação Alternativa e Aumentativa (CAA) para estudantes com TEA Nível 2 de Suporte.

ATRIBUTOS ATIVOS:
- perfil: B (Explorador Visual)
- formato_texto: fragmentado
- suporte_visual: alto
- sequencia_passos: sempre
- um_comando_por_vez: true
- densidade_texto: baixa
- ano_escolar: {ano_escolar}
- disciplina: {disciplina}

TAREFA:
Transforme o texto abaixo em um formato acessível para um estudante do {ano_escolar} com TEA Perfil B.

REGRAS OBRIGATÓRIAS:
1. Divida o conteúdo em blocos numerados sequencialmente (Passo 1, Passo 2...)
2. Cada bloco deve conter: UMA ideia + UMA imagem descrita + UMA palavra-chave destacada em MAIÚSCULAS
3. Frases com no máximo 10 palavras
4. Use verbos no imperativo claro: "Olhe", "Toque", "Escreva", "Circle"
5. Após cada bloco, adicione: 🌟 [reforço positivo variado: "Ótimo!", "Você fez isso!", "Perfeito!"]
6. Ao final, adicione um bloco "EU APRENDI:" com 3 palavras-chave do texto
7. Indique onde deve haver uma imagem real com: [IMAGEM: descrição detalhada para geração]
8. Nunca use negação ("não faça") — substitua por instrução afirmativa

TEXTO ORIGINAL:
{inserir texto aqui}

RESULTADO:
```

---

#### PROMPT-EBOOK-03 | Criação de capítulo de e-book do zero com tema âncora

```
Você é um autor especializado em materiais educativos inclusivos para estudantes com TEA no Ensino Fundamental.

ATRIBUTOS ATIVOS:
- perfil: {A | B}
- tema_ancora: {tema de interesse do aluno, ex: "dinossauros"}
- disciplina: {disciplina}
- conteudo_curricular: {ex: "frações", "substantivos", "ciclo da água"}
- ano_escolar: {ano_escolar}
- suporte_visual: {suporte_visual}
- linguagem_literal: {linguagem_literal}

TAREFA:
Crie um capítulo completo de e-book educativo que ensine o conteúdo curricular de {conteudo_curricular} usando {tema_ancora} como fio condutor da narrativa.

ESTRUTURA OBRIGATÓRIA DO CAPÍTULO:
1. TÍTULO — criativo, claro, com o tema âncora
2. O QUE VOCÊ VAI APRENDER HOJE — lista de 3 objetivos em linguagem de aluno
3. CONTEXTO — parágrafo curto conectando {tema_ancora} ao {conteudo_curricular}
4. DESENVOLVIMENTO — mínimo 3 seções com:
   - Explicação do conceito (linguagem {perfil})
   - Exemplo com {tema_ancora}
   - [IMAGEM: descrição para geração]
   - Box "CURIOSIDADE!" com fato relacionado
5. VAMOS PRATICAR — 2 atividades integradas (tipos conforme perfil)
6. EU SEI QUE APRENDI SE: — checklist de 4 itens autoavaliação
7. GLOSSÁRIO DO CAPÍTULO — máximo 5 termos explicados simplesmente

REGRAS DE LINGUAGEM:
- Perfil A: objetiva, literal, sem metáforas, vocabulário do {ano_escolar}
- Perfil B: frases curtas, pictogramas descritos, um conceito por vez

ESCREVA O CAPÍTULO COMPLETO:
```

---

### 🖼️ CATEGORIA 2: GERAÇÃO DE IMAGENS

---

#### PROMPT-IMG-01 | Imagem de ilustração para conteúdo educativo (Perfil A)

```
Crie uma ilustração educativa com as seguintes especificações:

CONTEXTO PEDAGÓGICO:
- Disciplina: {disciplina}
- Conteúdo: {conteudo_curricular}
- Tema âncora: {tema_ancora}
- Perfil do estudante: TEA Nível 1 — processamento visual bom, linguagem literal

ESPECIFICAÇÕES VISUAIS OBRIGATÓRIAS:
- Estilo: ilustração vetorial limpa, flat design, linhas definidas
- Fundo: branco ou cinza muito claro (#F5F5F5)
- Cores: paleta limitada a 4 cores máximo, sem gradientes complexos
- Texto na imagem: máximo 5 palavras, fonte sans-serif grande e legível
- Personagens: expressões faciais claras e explícitas (não ambíguas)
- Composição: um único elemento principal centralizado, sem poluição visual
- Sem: sombras complexas, perspectiva exagerada, múltiplas ações simultâneas

CONTEÚDO DA CENA:
{descreva a cena específica}

RESULTADO ESPERADO:
Imagem clara que um estudante com TEA Nível 1 consiga identificar o conceito de {conteudo_curricular} sem explicação verbal adicional.
```

---

#### PROMPT-IMG-02 | Pictograma e sequência visual (Perfil B)

```
Crie um conjunto de pictogramas sequenciais para comunicação alternativa e aumentativa (CAA):

CONTEXTO PEDAGÓGICO:
- Atividade: {nome_da_atividade}
- Disciplina: {disciplina}
- Perfil: TEA Nível 2 — comunicação visual, suporte alto

ESPECIFICAÇÕES DO CONJUNTO:
- Quantidade: {numero_de_etapas} pictogramas em sequência (ex: 4)
- Layout: horizontal ou vertical com seta de progressão entre cada um
- Estilo: pictograma minimalista estilo ARASAAC / Boardmaker
- Cada pictograma deve ter: ícone + palavra escrita abaixo (fonte grande, bold)
- Moldura numerada: 1 → 2 → 3 → 4 com cores progressivas (claro para intenso)
- Símbolo de conclusão no último: ✓ verde com estrela

ETAPAS A ILUSTRAR:
{liste cada etapa: ex: "1. Pegar o lápis / 2. Abrir o caderno / ..."}

ESPECIFICAÇÕES TÉCNICAS:
- Tamanho individual: 200x200px cada
- Contraste alto (WCAG AA mínimo)
- Sem detalhes desnecessários — mínimo viável para reconhecimento
- Teste visual: a imagem deve ser reconhecível em 2 segundos por uma criança de 8 anos
```

---

#### PROMPT-IMG-03 | Cena narrativa com tema âncora para e-book

```
Ilustração para página de e-book inclusivo:

ATRIBUTOS:
- tema_ancora: {ex: trens, robôs, animais, games}
- conteudo: {conteudo_curricular}
- perfil: {A | B}
- tom: acolhedor, sem elementos ameaçadores

CENA SOLICITADA:
{descreva a cena pedagógica específica conectando tema_ancora ao conteúdo}

ESTILO:
- Ilustração infantil digital, traço suave mas definido
- Personagem principal: {tema_ancora} realizado a tarefa de {conteudo_curricular}
- Expressão: positiva, focada, sem ambiguidade emocional
- Background: ambiente de aprendizagem (sala de aula, biblioteca, natureza)
- Sem: violência, conteúdo assustador, ambiguidade narrativa
- Proporção: 16:9 para e-book / 4:3 para atividade impressa

ELEMENTO EDUCATIVO VISÍVEL NA CENA:
Inclua de forma visível e legível na cena: {elemento visual do conteúdo, ex: "uma fração escrita num quadro"}

Resultado: Imagem que motive o estudante com TEA a engajar com o conteúdo através do tema de seu interesse.
```

---

### ✏️ CATEGORIA 3: CRIAÇÃO DE ATIVIDADES

---

#### PROMPT-ATI-01 | Criação de atividade completa (qualquer tipo)

```
Você é um psicopedagogo especializado em educação inclusiva e design de atividades para estudantes com TEA.

CONFIGURAÇÃO:
- perfil: {A | B}
- ano_escolar: {ano_escolar}
- disciplina: {disciplina}
- conteudo_curricular: {conteudo_curricular}
- tipo_atividade: {arrastar_soltar | multipla_escolha | dissertacao_simples | dissertacao_complexa | sequenciamento | pareamento | completar_lacunas | verdadeiro_falso}
- tema_ancora: {tema_ancora}
- modalidade_resposta: {modalidade_resposta}
- nivel_cognitivo: {identificar | compreender | aplicar | analisar}

TAREFA:
Crie uma atividade completa do tipo {tipo_atividade} para um estudante do {ano_escolar} com TEA Perfil {perfil}.

ESTRUTURA OBRIGATÓRIA DA ATIVIDADE:
───────────────────────────────────────
CABEÇALHO:
• Nome da atividade (com tema âncora se disponível)
• Objetivo de aprendizagem (1 frase)
• Tempo estimado: ___ minutos
• Materiais necessários (se houver)
───────────────────────────────────────
INSTRUÇÃO PARA O ESTUDANTE:
• Máximo 2 frases para Perfil A / 1 frase para Perfil B
• Verbo claro no início: "Leia e responda...", "Arraste...", "Escolha..."
• Para Perfil B: instrução também em pictograma [descreva o pictograma]
───────────────────────────────────────
CORPO DA ATIVIDADE:
{gerar conforme tipo escolhido — veja especificações por tipo abaixo}
───────────────────────────────────────
GABARITO / RESPOSTA ESPERADA:
• Resposta correta completa
• Para dissertação: critérios de avaliação (3 itens)
───────────────────────────────────────
ADAPTAÇÕES ADICIONAIS:
• Versão reduzida (50% da atividade para dias difíceis)
• Dica visual disponível (descrição do recurso de apoio)
• Critério de sucesso: o aluno aprende se ___
───────────────────────────────────────

ESPECIFICAÇÕES POR TIPO:
[arrastar_soltar]: crie pares/grupos, indique claramente o que vai para onde
[multipla_escolha]: 4 alternativas, distratores plausíveis mas claramente errados, sem pegadinhas
[dissertacao_simples]: 1 pergunta fechada, resposta de 1-3 linhas, modelo de resposta fornecido
[dissertacao_complexa]: 1 pergunta aberta, resposta de 5-10 linhas, scaffolding com frases-guia
[sequenciamento]: 4-6 passos fora de ordem para reorganizar
[pareamento]: 2 colunas de até 6 pares para conectar
[completar_lacunas]: texto com 3-5 lacunas + banco de palavras
[verdadeiro_falso]: 5-8 afirmações, sem dupla negação, linguagem literal

GERE A ATIVIDADE COMPLETA:
```

---

### 🔄 CATEGORIA 4: ADAPTAÇÃO DE ATIVIDADES EXISTENTES

---

#### PROMPT-ADAPT-01 | Converter atividade para formato Arrastar e Soltar

```
Você é um designer instrucional especializado em adaptação de atividades para estudantes com TEA.

ATRIBUTOS:
- perfil_destino: {A | B}
- suporte_visual: {suporte_visual}
- sequencia_passos: {sequencia_passos}
- um_comando_por_vez: {um_comando_por_vez}

ATIVIDADE ORIGINAL:
{cole aqui a atividade original}

TAREFA:
Adapte a atividade acima para o formato "arrastar e soltar" (drag-and-drop), adequada para plataforma digital ou impressa com recorte.

RESULTADO ESPERADO:

1. VERSÃO DIGITAL (HTML/plataforma):
   - Descreva os elementos que devem ser arrastáveis (cards/peças)
   - Descreva as áreas de destino (slots/caixas)
   - Indique feedback visual para acerto (✓ verde) e erro (X vermelho + nova tentativa)
   - Indique se há limite de tentativas
   - Descreva animação de sucesso ao completar (simples, não excessiva)

2. VERSÃO IMPRESSA (recorte e cole):
   - Liste os elementos para imprimir e recortar
   - Desenhe o layout da folha de destino com caixas nomeadas
   - Indique tamanho mínimo das peças (acessibilidade motora)
   - Sugira material: papel cartão ou laminado para durabilidade

3. INSTRUÇÕES PARA O ESTUDANTE:
   - Perfil A: "Leia cada [palavra/imagem] e arraste para onde ela pertence."
   - Perfil B: [pictograma da ação + 1 palavra-chave]

4. CRITÉRIO DE SUCESSO:
   - % de acertos para considerar domínio: __%
   - O que fazer com os erros: [tentativa novamente | professor intervém]

ATIVIDADE ADAPTADA:
```

---

#### PROMPT-ADAPT-02 | Converter atividade para Múltipla Escolha

```
Você é um especialista em avaliação inclusiva para TEA, com base em evidências do CAED-UFSM (2023) e REBENA (2024).

ATRIBUTOS:
- perfil_destino: {A | B}
- linguagem_literal: {linguagem_literal}
- densidade_texto: {densidade_texto}
- tema_ancora: {tema_ancora se houver}

ATIVIDADE ORIGINAL:
{cole aqui a atividade original}

TAREFA:
Adapte a atividade para o formato de múltipla escolha inclusivo para TEA.

REGRAS DE OURO PARA MÚLTIPLA ESCOLHA COM TEA:
⚠️ PROIBIDO: duplo sentido, pegadinhas, "exceto", "nunca", negações duplas
✅ OBRIGATÓRIO:
- Enunciado: máximo 2 frases, linguagem direta
- 4 alternativas sempre (A, B, C, D)
- Alternativas com tamanho similar (evitar a correta ser sempre a mais longa)
- Distratores plausíveis mas inequivocamente errados para quem aprendeu
- Uma e somente uma resposta correta
- Sem "todas as anteriores" ou "nenhuma das anteriores"

PARA PERFIL B — adicionalmente:
- Cada alternativa acompanhada de ícone/imagem descrita
- Alternativas curtas (máximo 6 palavras)
- Fonte recomendada: Arial ou Open Dyslexic, tamanho 16+

RESULTADO:

ENUNCIADO ADAPTADO:
{enunciado reescrito}

ALTERNATIVAS:
A) {alternativa com imagem se Perfil B: [IMAGEM: descrição]}
B) {alternativa}
C) {alternativa}
D) {alternativa}

RESPOSTA CORRETA: {letra}
JUSTIFICATIVA: {por que esta é a correta — para o professor}
DICA DE APOIO (se o aluno errar): {pista visual ou textual}

ATIVIDADE ADAPTADA:
```

---

#### PROMPT-ADAPT-03 | Converter atividade para Dissertação Simples

```
Você é um especialista em escrita adaptada para estudantes com TEA no Ensino Fundamental.

ATRIBUTOS:
- perfil_destino: {A | B}
- abertura_resposta: estruturada
- ano_escolar: {ano_escolar}
- scaffolding_nivel: {alto | médio | baixo}

ATIVIDADE ORIGINAL:
{cole aqui a atividade original}

TAREFA:
Adapte para dissertação simples com scaffolding (andaime) adequado ao perfil.

ESTRUTURA DA DISSERTAÇÃO ADAPTADA:

PERGUNTA PRINCIPAL:
{pergunta reescrita de forma direta e literal}

SCAFFOLDING — FRASES DE INÍCIO (o aluno completa):
"Eu aprendi que _______________________________________________."
"Um exemplo é ________________________________________________."
"Isso é importante porque _____________________________________."

ESPAÇO DE RESPOSTA:
[Para Perfil A]: Linhas em branco (espaço para 3-5 linhas)
[Para Perfil B]: Blocos de resposta com ícone e 1-2 linhas apenas

BANCO DE PALAVRAS DE APOIO (opcional para Perfil B):
{liste 5-8 palavras-chave do conteúdo que podem ser usadas}

CRITÉRIOS DE AVALIAÇÃO (para o professor):
• Critério 1 (conteúdo — 50%): {o que deve aparecer na resposta}
• Critério 2 (compreensão — 30%): {evidência de entendimento}  
• Critério 3 (esforço/participação — 20%): {produção mínima aceitável}

RESPOSTA MODELO (referência para o professor):
{escreva a resposta esperada completa}

ATIVIDADE ADAPTADA:
```

---

#### PROMPT-ADAPT-04 | Converter atividade para Dissertação Complexa

```
Você é um especialista em avaliação para TEA com foco em produção escrita estruturada.

ATRIBUTOS:
- perfil_destino: A (Leitor Silencioso — este formato é mais adequado ao Perfil A)
- abertura_resposta: semi_estruturada
- ano_escolar: {ano_escolar} — mínimo 5º ano para este formato
- nivel_cognitivo: {analisar | avaliar | criar}

ATIVIDADE ORIGINAL:
{cole aqui a atividade ou contexto}

TAREFA:
Transforme em dissertação complexa com estrutura de escrita guiada.

RESULTADO:

CONTEXTO INTRODUTÓRIO (leitura motivadora):
{parágrafo curto — 5 linhas máximo — sobre o tema, com linguagem literal}

PERGUNTA PRINCIPAL:
{pergunta aberta — máximo 3 linhas, sem duplo sentido}

PERGUNTAS-GUIA (scaffolding dissertação complexa):
Use estas perguntas para organizar sua resposta:
1. O que é {conceito principal}?
2. Como {conceito} aparece em {exemplo concreto}?
3. Por que {conceito} é importante no nosso dia a dia?
4. {pergunta de análise específica do conteúdo}

ORGANIZADOR VISUAL DA ESTRUTURA:
┌─────────────────────────────────┐
│ INTRODUÇÃO: escreva 1-2 frases  │
│ sobre o que você vai explicar   │
├─────────────────────────────────┤
│ DESENVOLVIMENTO: responda as    │
│ perguntas-guia, uma por vez     │
├─────────────────────────────────┤
│ CONCLUSÃO: escreva 1 frase com  │
│ o que você aprendeu             │
└─────────────────────────────────┘

ESPAÇO: _____ linhas (sugerido: 15-20)

CRITÉRIOS DE AVALIAÇÃO (4 pontos):
1. Responde à pergunta principal [0-1 ponto]
2. Usa pelo menos 2 perguntas-guia [0-1 ponto]
3. Linguagem clara e organizada [0-1 ponto]
4. Conclusão presente [0-1 ponto]

ATIVIDADE ADAPTADA:
```

---

#### PROMPT-ADAPT-05 | Converter atividade para Sequenciamento

```
Você é um designer instrucional especializado em atividades cognitivas para TEA com base no método TEACCH.

ATRIBUTOS:
- perfil_destino: {A | B}
- sequencia_passos: sempre
- suporte_visual: {suporte_visual}
- um_comando_por_vez: {um_comando_por_vez}

ATIVIDADE ORIGINAL:
{cole aqui o conteúdo ou a atividade}

TAREFA:
Crie uma atividade de sequenciamento (ordenação de etapas) baseada no conteúdo fornecido.

RESULTADO:

TÍTULO: "Coloque na ordem certa!"

INSTRUÇÃO:
[Perfil A]: "Leia as frases abaixo e escreva os números 1, 2, 3... para colocá-las na ordem correta."
[Perfil B]: [IMAGEM: mão segurando carta numerada] + "Numere as imagens na ordem certa."

ETAPAS FORA DE ORDEM (4 a 6 etapas):
□ ___ {etapa embaralhada 1}
□ ___ {etapa embaralhada 2}
□ ___ {etapa embaralhada 3}
□ ___ {etapa embaralhada 4}
□ ___ {etapa embaralhada 5 — opcional}
□ ___ {etapa embaralhada 6 — opcional}

PARA VERSÃO DIGITAL: Descreva os cards arrastáveis e a linha do tempo de destino.
PARA VERSÃO IMPRESSA: Descreva as tiras de papel numeráveis.

GABARITO (ordem correta):
1. {etapa 1}
2. {etapa 2}
3. {etapa 3}
4. {etapa 4}

REFORÇO POSITIVO AO CONCLUIR:
"Você ordenou tudo! Agora você sabe como {conceito} funciona passo a passo. ⭐"

ATIVIDADE ADAPTADA:
```

---

#### PROMPT-ADAPT-06 | Converter atividade para Completar Lacunas

```
ATRIBUTOS:
- perfil_destino: {A | B}
- linguagem_literal: {linguagem_literal}
- banco_palavras: true (sempre para TEA)
- numero_lacunas: {3 para Perfil B | 5 para Perfil A}

ATIVIDADE ORIGINAL:
{cole aqui o conteúdo}

TAREFA:
Crie uma atividade de completar lacunas inclusiva para TEA.

REGRAS:
- Escolha palavras-chave do conteúdo para as lacunas (substantivos/verbos centrais)
- Nunca remova palavras de ligação (artigos, preposições) — manter coesão
- Banco de palavras visível, com mais opções que lacunas (+2 distratores)
- Lacunas de tamanho padronizado (não revela o tamanho da resposta)
- Numere cada lacuna (___1___, ___2___)

RESULTADO:

BANCO DE PALAVRAS:
[ palavra1 | palavra2 | palavra3 | palavra4 | palavra5 | distrator1 | distrator2 ]

TEXTO COM LACUNAS:
{texto com ___N___ para cada lacuna, mínimo de contexto ao redor}

GABARITO:
1. {resposta}  2. {resposta}  3. {resposta}

ATIVIDADE ADAPTADA:
```

---

#### PROMPT-ADAPT-07 | Converter atividade para Pareamento

```
ATRIBUTOS:
- perfil_destino: {A | B}
- suporte_visual: {suporte_visual}
- numero_pares: {4 para Perfil B | 6 para Perfil A}

ATIVIDADE ORIGINAL:
{cole aqui o conteúdo}

TAREFA:
Crie uma atividade de pareamento (coluna A ↔ coluna B) para TEA.

REGRAS:
- Coluna A: termos, conceitos ou imagens (descritas)
- Coluna B: definições curtas, exemplos ou imagens complementares
- Items em ordem aleatória entre colunas
- Perfil A: conectar com linha / escrever número
- Perfil B: conectar com linha colorida / colar figurinha

RESULTADO:

INSTRUÇÃO: "Una cada item da COLUNA A com seu par na COLUNA B."
[Perfil B: adicione pictograma de "conectar" + seta]

COLUNA A | COLUNA B
---------|----------
1. {item} | A. {par}
2. {item} | B. {par}
3. {item} | C. {par}
4. {item} | D. {par}

GABARITO: 1-{letra} | 2-{letra} | 3-{letra} | 4-{letra}

ATIVIDADE ADAPTADA:
```

---

#### PROMPT-ADAPT-08 | Converter atividade para Verdadeiro ou Falso

```
ATRIBUTOS:
- perfil_destino: {A | B}
- linguagem_literal: true (sempre para este formato com TEA)
- numero_afirmacoes: {5 para Perfil B | 8 para Perfil A}

REGRAS OBRIGATÓRIAS — VERDADEIRO/FALSO COM TEA:
⚠️ JAMAIS use: "sempre", "nunca", "todos", "nenhum" como distratores únicos
⚠️ JAMAIS use: negação dupla ("não é falso que...")
⚠️ JAMAIS use: afirmações com dupla informação (verdadeiro + falso na mesma frase)
✅ USE: afirmações simples, diretas, com fato verificável

ATIVIDADE ORIGINAL:
{cole aqui o conteúdo}

RESULTADO:

INSTRUÇÃO: "Leia cada frase. Escreva V se for Verdadeiro ou F se for Falso."
[Perfil B: adicione ícone ✓ para V e ✗ para F com cores]

1. ___  {afirmação}
2. ___  {afirmação}
3. ___  {afirmação}
4. ___  {afirmação}
5. ___  {afirmação}

GABARITO: 1.{V/F} | 2.{V/F} | 3.{V/F} | 4.{V/F} | 5.{V/F}

PARA CADA FALSO — CORREÇÃO OPCIONAL:
"A afirmação {N} é FALSA porque: {explicação direta}"

ATIVIDADE ADAPTADA:
```

---

## PARTE 4 — ARQUITETURA DO REPOSITÓRIO `Edu-Adapt-AI`

---

```
C:\Repositorios\Edu-Adapt-AI\
│
├── README.md                          ← Visão geral do projeto + como usar
├── PROMPTS_MASTER.md                  ← Este arquivo (todos os prompts)
├── ATRIBUTOS_PERFIS.md                ← Tabela de atributos por perfil
│
├── /profiles/                         ← Definição JSON dos perfis
│   ├── perfil-A.json                  ← Leitor Silencioso (TEA Nível 1)
│   └── perfil-B.json                  ← Explorador Visual (TEA Nível 2)
│
├── /prompts/                          ← Prompts por categoria
│   ├── /ebook/
│   │   ├── EBOOK-01-reescrita-perfil-A.md
│   │   ├── EBOOK-02-reescrita-perfil-B.md
│   │   └── EBOOK-03-criacao-tema-ancora.md
│   ├── /imagens/
│   │   ├── IMG-01-ilustracao-perfil-A.md
│   │   ├── IMG-02-pictograma-sequencia-perfil-B.md
│   │   └── IMG-03-cena-narrativa.md
│   ├── /atividades/
│   │   └── ATI-01-criacao-qualquer-tipo.md
│   └── /adaptacoes/
│       ├── ADAPT-01-arrastar-soltar.md
│       ├── ADAPT-02-multipla-escolha.md
│       ├── ADAPT-03-dissertacao-simples.md
│       ├── ADAPT-04-dissertacao-complexa.md
│       ├── ADAPT-05-sequenciamento.md
│       ├── ADAPT-06-completar-lacunas.md
│       ├── ADAPT-07-pareamento.md
│       └── ADAPT-08-verdadeiro-falso.md
│
├── /atividades/                       ← Atividades já geradas e prontas
│   ├── /matematica/
│   │   ├── /fracoes/
│   │   │   ├── perfil-A-multipla-escolha.md
│   │   │   ├── perfil-B-arrastar-soltar.md
│   │   │   └── perfil-A-dissertacao-simples.md
│   │   └── /multiplicacao/ ...
│   ├── /portugues/
│   │   ├── /substantivos/ ...
│   │   └── /pontuacao/ ...
│   ├── /ciencias/ ...
│   ├── /historia/ ...
│   └── /geografia/ ...
│
├── /ebook/                            ← Capítulos de e-book gerados
│   ├── /matematica/ ...
│   ├── /portugues/ ...
│   └── /template-capitulo.md         ← Template em branco para novos capítulos
│
├── /imagens/                          ← Prompts de imagem prontos por atividade
│   ├── /pictogramas/ ...
│   └── /ilustracoes/ ...
│
├── /ferramentas/                      ← Scripts e utilitários
│   ├── gerador-atributos.js           ← Gera bloco de atributos preenchido
│   ├── seletor-prompt.md              ← Árvore de decisão: qual prompt usar
│   └── validador-inclusividade.md     ← Checklist para revisar material gerado
│
└── /documentacao/
    ├── fundamentacao-clinica.md       ← Referências: DSM-5, TEACCH, ABA, PECS
    ├── guia-professor.md              ← Como usar o sistema em sala de aula
    └── PUCPR-projeto-extensao.md      ← Ligação com o projeto acadêmico
```

---

## PARTE 5 — LISTA PRIORIZADA DE ATIVIDADES PARA O REPOSITÓRIO

### Por Categoria e Nível — Do mais simples ao mais complexo

```
PRIORIDADE ALTA (implementar primeiro — maior impacto):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CAT-1] Arrastar e Soltar
 → Matemática: ordenar números, agrupar figuras geométricas
 → Português: montar sílabas, classificar palavras
 → Ciências: montar ciclo da água, cadeia alimentar

[CAT-2] Múltipla Escolha
 → Todas as disciplinas, todos os anos (formato mais versátil)
 → Português 4º ano: identificar substantivos
 → Matemática 5º ano: frações simples
 → Ciências 6º ano: sistema solar

[CAT-3] Verdadeiro ou Falso
 → Alta velocidade de implementação
 → Bom para revisão e avaliação diagnóstica
 → Todas as disciplinas

PRIORIDADE MÉDIA (segunda rodada):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CAT-4] Sequenciamento
 → Ciências: fases da vida dos animais, experimentos
 → História: linha do tempo de eventos
 → Português: ordenar parágrafos de texto

[CAT-5] Pareamento
 → Matemática: figura geométrica ↔ nome
 → Ciências: animal ↔ habitat
 → Português: antônimos e sinônimos
 → Geografia: país ↔ capital

[CAT-6] Completar Lacunas
 → Português: concordância, ortografia
 → Ciências: conceitos-chave
 → Matemática: tabuada, propriedades

PRIORIDADE BAIXA (após consolidação):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[CAT-7] Dissertação Simples
 → Perfil A prioritariamente
 → A partir do 4º ano

[CAT-8] Dissertação Complexa
 → Perfil A, 6º e 7º ano
 → Últimas a implementar

[CAT-9] Capítulos de E-book
 → Paralelo à implementação das atividades
 → Começar pelo tema âncora mais frequente nos alunos
```

---

## PARTE 6 — ÁRVORE DE DECISÃO: QUAL PROMPT USAR?

```
Você tem um CONTEÚDO e precisa criar algo para um estudante com TEA?
                               │
            ┌──────────────────┴──────────────────┐
            │                                     │
     Tem um TEXTO PRONTO?                  Precisa criar DO ZERO?
       (reescrever/adaptar)               (novo conteúdo)
            │                                     │
     ┌──────┴──────┐                    ┌──────────┴──────────┐
     │             │                   │                     │
   Perfil A      Perfil B          É E-BOOK?           É ATIVIDADE?
     │             │                   │                     │
EBOOK-01       EBOOK-02          EBOOK-03              ATI-01
                                                           │
                                            Que TIPO de atividade?
                                            ┌──────────────┼──────────────┐
                                     Arrastar    Múltipla   Dissertação  Outros
                                     Soltar      Escolha    (simples/    (sequência,
                                     ADAPT-01   ADAPT-02    complexa)   pareamento,
                                                           ADAPT-03/04  lacunas, V/F)
                                                                       ADAPT 05-08
```

---

## PARTE 7 — CHECKLIST DE VALIDAÇÃO DE MATERIAL INCLUSIVO

*Use antes de incluir qualquer material no repositório*

```
✅ CHECKLIST DE INCLUSIVIDADE TEA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
□ Linguagem literal (sem metáforas, ironias, duplo sentido)
□ Frases curtas (máximo 20 palavras para Perfil A / 10 para Perfil B)
□ Um conceito por vez (sem sobrecarga cognitiva)
□ Instruções claras com verbo no início
□ Resposta única e inequívoca (exceto dissertação)
□ Suporte visual descrito ou incluído
□ Tema âncora integrado (se disponível)
□ Reforço positivo presente
□ Versão reduzida disponível
□ Gabarito ou critérios de avaliação incluídos
□ Vocabulário adequado ao ano escolar
□ Nenhuma negação dupla
□ Nenhuma "pegadinha" ou ambiguidade intencional
□ Espaço de resposta adequado ao tipo
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Score: ___/14  |  Mínimo para publicar: 12/14
```

---

## REFERÊNCIAS CLÍNICAS E PEDAGÓGICAS

1. **DSM-5-TR** (APA, 2022) — Classificação dos níveis de suporte TEA  
2. **PINTO, J.C. et al.** (2024) — Adaptação curricular e TEA. REBENA, v.9, p.495-503  
3. **CAED-UFSM** (2023) — Guia TEA na Educação Profissional e Superior  
4. **ROSSETTO, T.; MARCON, K.** (2024) — Tecnologia Assistiva e TEA. Rev. Eletr. Educação, v.18  
5. **REASE** (2024) — Tecnologias assistivas na inclusão de alunos com TEA. v.10, n.10  
6. **SCHOPLER, E.** — Método TEACCH: estrutura, previsibilidade e apoio visual  
7. **FONTENELE; LOURINHO** (2020) — Neurociência, TEA e formação de professores. BJD, v.6  
8. **UFSM/SAEST** (2024) — Cartilha TEA: orientações pedagógicas para professores  

---

*Documento gerado para o projeto de Prática Extensionista PUCPR*  
*Sistema Edu-Adapt-AI | Repositório: `C:\Repositorios\Edu-Adapt-AI`*  
*Versão 1.0 | Junho 2026*
