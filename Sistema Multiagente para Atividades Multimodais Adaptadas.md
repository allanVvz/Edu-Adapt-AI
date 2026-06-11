# EduAdapt IA — Sistema Multiagente para Atividades Multimodais Adaptadas

## 1. Visão Geral

O **EduAdapt IA** é um sistema web multiagente criado para receber atividades escolares do Ensino Fundamental e transformá-las em atividades multimodais, adaptadas ao perfil pedagógico de cada aluno.

A proposta central é permitir que uma atividade comum, como uma questão de múltipla escolha, uma pergunta dissertativa, uma atividade de associação ou uma brincadeira pedagógica, seja convertida em diferentes formas de visualização, interação e execução.

O sistema deve ser capaz de:

* Cadastrar atividades escolares.
* Cadastrar perfis de alunos.
* Relacionar dificuldades do aluno com estratégias de adaptação.
* Processar atividades por agentes de IA.
* Gerar novas modalidades da mesma atividade.
* Validar a qualidade da adaptação.
* Permitir reprocessamento com feedback.
* Exportar atividades para visualização digital ou impressão.
* Integrar com bases externas, APIs e bancos de dados.
* Rodar em ambiente Docker, com serviços internos e modularizados.

---

## 2. Objetivo do Projeto

Construir uma aplicação web capaz de transformar atividades escolares tradicionais em experiências pedagógicas multifacetadas, acessíveis e adaptáveis.

Uma mesma atividade poderá gerar diferentes versões, como:

* Múltipla escolha.
* Dissertativa simplificada.
* Arrastar e soltar.
* Associação de imagens.
* Atividade com apoio visual.
* Atividade com áudio.
* Atividade com vídeo.
* Atividade em formato de brincadeira.
* Atividade impressa em folha.
* Atividade em etapas guiadas.
* Atividade com pictogramas.
* Atividade com menor carga cognitiva.

O sistema deve adaptar a atividade conforme o perfil do aluno, considerando suas dificuldades, necessidades e formas mais adequadas de interação.

---

## 3. Conceito Principal

Cada atividade será tratada como um objeto pedagógico estruturado.

Ela terá:

* Pergunta.
* Resposta esperada.
* Modalidade.
* Tipo de execução.
* Grau de dificuldade.
* Perfil de aluno recomendado.
* Status de validação.
* Histórico de versões.
* Arquivos relacionados.
* Avaliação humana.
* Avaliação automática por agentes.

Exemplo conceitual:

```json
{
  "atividade": "Associe os animais ao local onde vivem.",
  "tipo": "associacao",
  "modalidades": ["visual", "arrastar", "impressao"],
  "ano": "2º ano",
  "disciplina": "Ciências",
  "dificuldade": 2,
  "perfil_aluno": "TEA - baixa tolerância a estímulos visuais",
  "status": "aprovada"
}
```

---

## 4. Público-Alvo

O sistema será utilizado principalmente por:

* Professores.
* Educadores de apoio.
* Coordenadores pedagógicos.
* Escolas.
* Projetos de inclusão.
* Equipes que trabalham com educação especial.
* Sistemas externos que desejam gerar atividades adaptadas via API.

O aluno não precisa necessariamente interagir diretamente com o sistema administrativo. O professor pode gerar, revisar, imprimir ou aplicar a atividade em outro ambiente.

---

## 5. Perfis de Alunos

O backend precisa entender perfis pedagógicos de alunos.

Esses perfis não devem ser tratados como diagnósticos clínicos, mas como conjuntos de características educacionais relevantes para adaptação da atividade.

Cada perfil pode conter:

* Nome do perfil.
* Ano escolar.
* Dificuldades principais.
* Preferências de interação.
* Recursos recomendados.
* Recursos a evitar.
* Nível de leitura.
* Nível de autonomia.
* Tipo de apoio necessário.
* Observações pedagógicas.

Exemplo:

```json
{
  "nome": "Perfil TEA - Alfabetização Inicial",
  "ano": "2º ano",
  "dificuldades": [
    "interpretação de enunciados longos",
    "excesso de estímulos visuais",
    "atividades com muitas etapas"
  ],
  "estrategias_recomendadas": [
    "frases curtas",
    "apoio visual",
    "uma instrução por vez",
    "fundo neutro",
    "poucas alternativas"
  ],
  "evitar": [
    "muitas cores simultâneas",
    "textos longos",
    "instruções abstratas",
    "mais de uma tarefa por bloco"
  ]
}
```

---

## 6. Tipos de Atividades

O sistema deve suportar múltiplos tipos de atividade.

### 6.1 Múltipla Escolha

Atividade com uma pergunta e alternativas.

Exemplo:

```text
Qual animal vive na água?

A) Cachorro
B) Peixe
C) Gato
```

Possíveis adaptações:

* Reduzir alternativas.
* Adicionar imagens.
* Aumentar espaçamento.
* Ler alternativas em áudio.
* Usar botões grandes.
* Transformar em escolha visual.

---

### 6.2 Dissertativa

Atividade em que o aluno responde com texto, fala, desenho ou mediação do professor.

Exemplo:

```text
Explique o que acontece com a água quando ela ferve.
```

Possíveis adaptações:

* Transformar em resposta curta.
* Transformar em completar frase.
* Permitir resposta oral.
* Permitir escolha entre imagens.
* Dividir em etapas.

---

### 6.3 Associação

Atividade de ligar, combinar, parear ou relacionar elementos.

Exemplo:

```text
Ligue o animal ao lugar onde ele vive.
```

Possíveis adaptações:

* Arrastar e soltar.
* Ligar com setas.
* Usar cartões físicos.
* Usar pictogramas.
* Separar em colunas.

---

### 6.4 Arrastar e Soltar

Atividade interativa em que o aluno movimenta elementos na tela.

Exemplo:

```text
Arraste os animais para Água ou Terra.
```

Possíveis adaptações:

* Reduzir número de itens.
* Usar categorias visuais.
* Usar feedback sonoro.
* Usar áreas grandes de destino.
* Evitar excesso de movimento.

---

### 6.5 Atividade de Brincadeira

Atividade pedagógica convertida em jogo simples ou dinâmica lúdica.

Exemplo:

```text
Use cartas coloridas para formar contas de adição.
```

Possíveis adaptações:

* Cartas.
* Memória.
* Sequência.
* Pareamento.
* Classificação.
* Jogo de escolha.
* Atividade com objetos concretos.

---

### 6.6 Atividade Impressa

Versão da atividade para folha de papel.

Características:

* Sem áudio.
* Sem interação digital.
* Layout visual claro.
* Espaçamento amplo.
* Fonte legível.
* Baixa poluição visual.
* Instruções curtas.
* Imagens grandes.
* Área de resposta bem definida.

---

## 7. Modalidades de Saída

Uma atividade original poderá gerar diferentes modalidades.

### 7.1 Modalidade Texto Adaptado

Gera uma versão mais clara e acessível do enunciado.

Exemplo:

```text
OBSERVE OS ANIMAIS.

CIRCULE O ANIMAL QUE VIVE NA ÁGUA.
```

---

### 7.2 Modalidade Visual

Gera uma versão com imagens, ícones, pictogramas ou cartões.

Exemplo:

```text
[PEIXE] [CACHORRO] [GATO]

CIRCULE QUEM VIVE NA ÁGUA.
```

---

### 7.3 Modalidade Áudio

Gera roteiro ou arquivo de áudio com leitura guiada.

Exemplo:

```text
Agora observe os animais.
Procure o animal que vive na água.
Circule o peixe.
```

---

### 7.4 Modalidade Interativa

Gera estrutura para atividade digital.

Exemplo:

```json
{
  "tipo": "drag_and_drop",
  "itens": ["peixe", "cachorro", "gato"],
  "destinos": ["água", "terra"]
}
```

---

### 7.5 Modalidade Impressão

Gera uma view própria para impressão.

Essa view deve ser diferente da tela digital.

Ela deve priorizar:

* Clareza.
* Alto contraste.
* Poucos elementos.
* Margens adequadas.
* Cabeçalho simples.
* Imagens grandes.
* Espaço para resposta.
* Ausência de elementos interativos digitais.

---

## 8. Tela Principal

A tela principal deve listar todas as atividades cadastradas.

Ela precisa ser:

* Clara.
* Amigável.
* Visualmente acessível.
* Levemente infantil, mas não caricata.
* Fácil para professores usarem.
* Organizada por filtros.

### Elementos da tela principal

* Lista de atividades.
* Botão “Nova Atividade”.
* Botão “Novo Perfil de Aluno”.
* Filtros por:

  * Disciplina.
  * Ano.
  * Tipo de atividade.
  * Modalidade.
  * Status.
  * Perfil de aluno.
  * Nível de dificuldade.
* Busca por texto.
* Cards de atividade.
* Status visual de aprovação.
* Acesso rápido para visualizar, editar, processar ou exportar.

### Exemplo de card de atividade

```text
Ciências — 2º ano
Associe os animais ao ambiente onde vivem

Tipo: Associação
Modalidades: Visual, Arrastar, Impressão
Dificuldade: 2/5
Status: Aprovada
Perfil recomendado: TEA - apoio visual
```

---

## 9. Cadastro de Atividades

O sistema deve ter uma área para cadastrar atividades.

Campos principais:

* Título da atividade.
* Disciplina.
* Ano escolar.
* Conteúdo.
* Pergunta.
* Resposta esperada.
* Tipo de atividade.
* Modalidade original.
* Nível de dificuldade.
* Texto da atividade.
* Arquivos anexos.
* Áudio original, se houver.
* Imagem original, se houver.
* PDF original, se houver.
* Observações do professor.

### Entrada possível

O professor poderá:

* Colar o texto da atividade.
* Fazer upload de PDF.
* Fazer upload de imagem.
* Fazer upload de áudio.
* Cadastrar manualmente pergunta e resposta.
* Importar atividade de API externa.
* Importar atividade de uma base conectada.

---

## 10. Cadastro de Perfis de Alunos

O sistema deve permitir o cadastro de perfis pedagógicos.

Campos recomendados:

* Nome do perfil.
* Ano/série.
* Nível de leitura.
* Nível de autonomia.
* Dificuldades principais.
* Estratégias recomendadas.
* Recursos visuais recomendados.
* Recursos sonoros recomendados.
* Recursos a evitar.
* Observações do professor.
* Preferência de modalidade.
* Histórico de atividades aprovadas.

Exemplo:

```json
{
  "nome": "Aluno com dificuldade de leitura",
  "ano": "3º ano",
  "nivel_leitura": "baixo",
  "dificuldades": [
    "enunciados longos",
    "vocabulário abstrato"
  ],
  "estrategias": [
    "frases curtas",
    "imagem de apoio",
    "exemplo antes da tarefa"
  ],
  "modalidades_preferidas": [
    "visual",
    "áudio",
    "múltipla escolha"
  ]
}
```

---

## 11. Pipeline Multiagente

O processamento da atividade deve ser feito por uma pipeline orquestrada.

Fluxo principal:

```text
Atividade cadastrada
        ↓
Agente Orquestrador
        ↓
Agente Leitor de Atividade
        ↓
Agente Classificador Pedagógico
        ↓
Agente de Perfil do Aluno
        ↓
Agente Adaptador Cognitivo
        ↓
Agente Gerador de Modalidades
        ↓
Agente de Áudio
        ↓
Agente de Imagem/Layout
        ↓
Agente de Interação
        ↓
Agente Validador
        ↓
Revisão Humana
        ↓
Exportação
```

---

## 12. Agentes do Sistema

### 12.1 Agente Orquestrador

Responsável por coordenar todos os demais agentes.

Funções:

* Receber a atividade.
* Identificar quais agentes serão acionados.
* Controlar ordem de execução.
* Consolidar resultados.
* Enviar para validação.
* Permitir reprocessamento com feedback.

Arquivo sugerido:

```text
/packages/agents/orchestrator.agent.ts
```

---

### 12.2 Agente Leitor de Atividade

Responsável por interpretar a atividade original.

Funções:

* Ler texto.
* Interpretar PDF.
* Interpretar imagem.
* Extrair pergunta.
* Extrair resposta.
* Identificar tipo de tarefa.
* Identificar elementos pedagógicos.

Arquivo sugerido:

```text
/packages/agents/activity-reader.agent.ts
```

---

### 12.3 Agente Classificador Pedagógico

Responsável por classificar a atividade.

Funções:

* Identificar disciplina.
* Identificar ano provável.
* Identificar objetivo pedagógico.
* Identificar habilidade ou competência associada.
* Pontuar complexidade.
* Sugerir tipo de adaptação.

Arquivo sugerido:

```text
/packages/agents/pedagogical-classifier.agent.ts
```

---

### 12.4 Agente de Perfil do Aluno

Responsável por relacionar atividade com perfil pedagógico.

Funções:

* Ler o perfil cadastrado.
* Identificar dificuldades relevantes.
* Selecionar estratégias de adaptação.
* Definir restrições.
* Definir modalidades recomendadas.

Arquivo sugerido:

```text
/packages/agents/student-profile.agent.ts
```

---

### 12.5 Agente Adaptador Cognitivo

Responsável por adaptar o conteúdo textual.

Funções:

* Simplificar enunciados.
* Reduzir carga cognitiva.
* Dividir instruções em etapas.
* Ajustar vocabulário.
* Reescrever perguntas.
* Criar exemplos.
* Reduzir alternativas quando necessário.

Arquivo sugerido:

```text
/packages/agents/cognitive-adapter.agent.ts
```

---

### 12.6 Agente Gerador de Modalidades

Responsável por criar diferentes versões da atividade.

Funções:

* Criar versão múltipla escolha.
* Criar versão dissertativa simplificada.
* Criar versão de associação.
* Criar versão de arrastar e soltar.
* Criar versão visual.
* Criar versão impressa.
* Criar versão em brincadeira.

Arquivo sugerido:

```text
/packages/agents/modality-generator.agent.ts
```

---

### 12.7 Agente de Áudio

Responsável por gerar estrutura de áudio.

Funções:

* Criar roteiro de narração.
* Definir pausas.
* Criar instruções faladas.
* Gerar áudio com modelo TTS.
* Avaliar clareza do áudio.

Arquivo sugerido:

```text
/packages/agents/audio-generator.agent.ts
```

Prompt separado:

```text
/packages/prompts/audio/generate-audio.prompt.md
```

Configuração do modelo:

```text
/packages/prompts/audio/model.config.json
```

---

### 12.8 Agente de Imagem e Layout

Responsável por gerar imagens, pictogramas e layouts.

Funções:

* Definir imagens necessárias.
* Gerar prompts de imagem.
* Definir layout da folha.
* Definir layout digital.
* Criar estrutura visual para impressão.
* Criar view para atividade interativa.

Arquivo sugerido:

```text
/packages/agents/image-layout-generator.agent.ts
```

Prompts separados:

```text
/packages/prompts/image/generate-activity-image.prompt.md
/packages/prompts/image/generate-print-layout.prompt.md
/packages/prompts/image/generate-card-visual.prompt.md
```

Configuração do modelo:

```text
/packages/prompts/image/model.config.json
```

---

### 12.9 Agente de Interação

Responsável por gerar atividades digitais interativas.

Funções:

* Criar estrutura de drag and drop.
* Criar estrutura de associação.
* Criar estrutura de seleção.
* Criar estrutura de ordenação.
* Criar feedback visual.
* Criar feedback sonoro opcional.

Arquivo sugerido:

```text
/packages/agents/interaction-generator.agent.ts
```

---

### 12.10 Agente Validador

Responsável por avaliar a qualidade da atividade gerada.

Funções:

* Validar clareza.
* Validar acessibilidade.
* Validar preservação pedagógica.
* Validar nível de dificuldade.
* Validar adequação ao perfil.
* Validar áudio.
* Validar imagem.
* Validar impressão.
* Gerar nota.
* Indicar aprovação ou reprovação.

Arquivo sugerido:

```text
/packages/agents/validator.agent.ts
```

---

## 13. Sistema de Validação

Cada atividade processada deve ser avaliada.

A validação deve considerar:

* A atividade ficou clara?
* A adaptação respeita o perfil?
* O objetivo pedagógico foi preservado?
* A dificuldade ficou adequada?
* A modalidade escolhida faz sentido?
* A imagem ficou adequada?
* O áudio ficou compreensível?
* A versão impressa está funcional?
* A atividade pode ser aplicada em sala?
* Precisa de revisão humana?

### Status possíveis

```text
rascunho
processando
gerada
em_revisao
aprovada
reprovada
reprocessar
exportada
```

### Motivos de reprovação

```text
audio_ruim
imagem_inadequada
adaptacao_ruim
dificuldade_inadequada
nao_preserva_objetivo
layout_confuso
atividade_muito_facil
atividade_muito_dificil
erro_pedagogico
erro_tecnico
```

Exemplo:

```json
{
  "status": "reprovada",
  "motivos": [
    "adaptacao_ruim",
    "layout_confuso"
  ],
  "feedback": "A atividade ficou visualmente poluída e perdeu parte do objetivo original.",
  "acao_recomendada": "reprocessar"
}
```

---

## 14. Reprocessamento com Feedback

Quando uma atividade for reprovada, o usuário poderá enviar feedback.

Exemplo:

```text
A imagem ficou muito infantil.
O áudio está rápido.
A atividade ficou fácil demais.
A pergunta perdeu o objetivo original.
```

O feedback deve ser enviado novamente para o Agente Orquestrador.

Fluxo:

```text
Atividade gerada
        ↓
Validação automática
        ↓
Revisão humana
        ↓
Reprovada com feedback
        ↓
Reprocessamento
        ↓
Nova versão
        ↓
Nova validação
```

Cada nova versão deve ser salva no histórico.

---

## 15. Histórico de Versões

Toda atividade processada deve manter versões.

Exemplo:

```text
Atividade Original
Versão 1 — Gerada automaticamente
Versão 2 — Reprocessada por feedback de áudio
Versão 3 — Aprovada para impressão
```

Cada versão deve guardar:

* Entrada usada.
* Perfil usado.
* Agentes executados.
* Prompts usados.
* Modelo usado.
* Saída gerada.
* Feedback recebido.
* Status.
* Data de criação.

---

## 16. Golden Dataset

O golden dataset será a base de exemplos validados do sistema.

Ele deve conter atividades aprovadas e revisadas, usadas como referência para novas gerações.

### Função do Golden Dataset

* Servir como benchmark.
* Servir como base de exemplos.
* Ajudar na avaliação automática.
* Melhorar consistência das adaptações.
* Permitir comparação entre versões.
* Apoiar reprocessamento.
* Formar memória pedagógica do sistema.

### Estrutura recomendada

```json
{
  "id": "CIE_2ANO_TEA_001",
  "atividade_original": {
    "titulo": "Animais e ambientes",
    "disciplina": "Ciências",
    "ano": "2º ano",
    "texto": "Classifique os animais em terrestres e aquáticos."
  },
  "perfil": {
    "tipo": "TEA",
    "necessidades": [
      "apoio visual",
      "frases curtas",
      "baixa carga visual"
    ]
  },
  "saida_aprovada": {
    "modalidade": "visual",
    "texto": "OBSERVE OS ANIMAIS. CIRCULE OS QUE VIVEM NA ÁGUA.",
    "layout": "duas colunas com imagens grandes",
    "interacao": "seleção visual"
  },
  "rubrica": {
    "clareza": 5,
    "acessibilidade": 5,
    "preserva_objetivo": 5,
    "dificuldade": 3,
    "adequacao_visual": 5
  },
  "status": "golden_aprovado"
}
```

---

## 17. Onde Armazenar o Golden Dataset

O golden dataset deve existir em duas camadas.

### 17.1 Banco de Dados

Usado pelo sistema em produção.

Tabelas sugeridas:

```text
golden_cases
golden_versions
golden_reviews
golden_embeddings
golden_rubrics
```

Vantagens:

* Busca rápida.
* Filtros por disciplina.
* Filtros por perfil.
* Busca semântica.
* Uso pelos agentes.
* Dashboard de qualidade.

---

### 17.2 Arquivos Versionados

Usado para controle técnico e versionamento.

Estrutura:

```text
/datasets/golden/
  /v0.1/
    cases.jsonl
    rubrics.yaml
    examples.md
    README.md
  /v0.2/
    cases.jsonl
    rubrics.yaml
    examples.md
    README.md
```

O banco guarda o uso operacional.

O Git guarda a versão oficial e auditável.

---

## 18. Integração com Bases Externas

O sistema deve ser integrável com fontes externas de atividades.

Exemplos:

* API própria.
* AI Brain.
* Banco PostgreSQL externo.
* Banco Supabase externo.
* Google Drive.
* Planilhas.
* CSV.
* JSON.
* Sistema escolar.
* Repositório de atividades.

### Funcionalidades de integração

* Cadastrar conexão externa.
* Testar conexão.
* Importar atividades.
* Mapear campos.
* Sincronizar dados.
* Exportar atividades processadas.
* Registrar logs.

Exemplo de conexão:

```json
{
  "nome": "AI Brain",
  "tipo": "api",
  "base_url": "https://api.exemplo.com",
  "auth_type": "bearer_token",
  "status": "ativa"
}
```

---

## 19. Exportação

Depois que uma atividade for processada, ela deve poder ser exportada.

### Formatos de exportação

* PDF para impressão.
* HTML visual.
* JSON estruturado.
* Markdown.
* Pacote de mídia.
* Atividade interativa.
* Áudio.
* Imagem.
* ZIP com todos os arquivos.

### Exportação para impressão

A exportação para impressão deve gerar uma nova view da atividade.

Essa view não deve simplesmente imprimir a tela.

Ela deve ser uma versão própria para papel.

Características:

* A4.
* Margens adequadas.
* Instruções claras.
* Imagens grandes.
* Fonte legível.
* Sem botões.
* Sem menus.
* Sem áudio.
* Sem elementos de interface.
* Espaço para resposta.
* Rodapé opcional com identificação da atividade.

---

## 20. Arquitetura Técnica

### Stack recomendada

```text
Frontend:
Next.js

Backend:
FastAPI

Banco:
PostgreSQL + pgvector

Storage:
MinIO ou Supabase Storage self-hosted

Fila:
Redis

Workers:
Celery ou BullMQ

Agentes:
OpenAI Agents SDK, LangGraph ou camada própria de orquestração

Automação:
n8n

Deploy:
Docker Compose

Proxy:
Nginx ou Traefik

Versionamento:
Git

Formato do golden dataset:
JSONL + YAML + Markdown
```

---

## 21. Docker

Todo o sistema deve rodar com Docker.

Serviços iniciais:

```text
web
api
postgres
redis
minio
worker
n8n
nginx
```

Exemplo conceitual:

```yaml
services:
  web:
    build: ./apps/web
    ports:
      - "3000:3000"

  api:
    build: ./apps/api
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - minio

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: eduadapt
      POSTGRES_USER: eduadapt
      POSTGRES_PASSWORD: eduadapt

  redis:
    image: redis:7

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"

  worker:
    build: ./apps/api
    command: celery -A app.worker worker --loglevel=info
    depends_on:
      - redis
      - postgres

  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
```

---

## 22. Estrutura de Pastas

```text
eduadapt-ai/
│
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── features/
│   │   │   ├── activities/
│   │   │   ├── student-profiles/
│   │   │   ├── exports/
│   │   │   └── integrations/
│   │   └── lib/
│   │
│   └── api/
│       ├── app/
│       │   ├── routes/
│       │   ├── services/
│       │   ├── agents/
│       │   ├── schemas/
│       │   ├── models/
│       │   ├── workers/
│       │   └── storage/
│       └── tests/
│
├── packages/
│   ├── prompts/
│   │   ├── audio/
│   │   │   ├── generate-audio.prompt.md
│   │   │   └── model.config.json
│   │   ├── image/
│   │   │   ├── generate-activity-image.prompt.md
│   │   │   ├── generate-print-layout.prompt.md
│   │   │   └── model.config.json
│   │   ├── adaptation/
│   │   │   ├── adapt-cognitive.prompt.md
│   │   │   └── model.config.json
│   │   └── validation/
│   │       ├── validate-activity.prompt.md
│   │       └── rubric.yaml
│   │
│   ├── schemas/
│   │   ├── activity.schema.json
│   │   ├── student-profile.schema.json
│   │   ├── modality.schema.json
│   │   └── validation.schema.json
│   │
│   └── evaluators/
│       ├── clarity.evaluator.ts
│       ├── accessibility.evaluator.ts
│       └── difficulty.evaluator.ts
│
├── datasets/
│   └── golden/
│       ├── v0.1/
│       │   ├── cases.jsonl
│       │   ├── rubrics.yaml
│       │   ├── examples.md
│       │   └── README.md
│       └── README.md
│
├── workflows/
│   └── n8n/
│       ├── import-activities.json
│       ├── export-approved-activity.json
│       └── review-feedback-flow.json
│
├── infra/
│   ├── docker-compose.yml
│   ├── nginx/
│   ├── postgres/
│   └── minio/
│
└── docs/
    ├── architecture.md
    ├── agent-flow.md
    ├── golden-dataset.md
    ├── database.md
    ├── integrations.md
    └── privacy.md
```

---

## 23. Modelagem Inicial do Banco

### Tabela: activities

```sql
CREATE TABLE activities (
  id UUID PRIMARY KEY,
  title TEXT NOT NULL,
  discipline TEXT,
  school_year TEXT,
  original_text TEXT,
  expected_answer TEXT,
  activity_type TEXT,
  original_modality TEXT,
  difficulty_level INTEGER,
  status TEXT DEFAULT 'draft',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### Tabela: student_profiles

```sql
CREATE TABLE student_profiles (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  school_year TEXT,
  reading_level TEXT,
  autonomy_level TEXT,
  difficulties JSONB,
  recommended_strategies JSONB,
  avoid_strategies JSONB,
  preferred_modalities JSONB,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### Tabela: activity_versions

```sql
CREATE TABLE activity_versions (
  id UUID PRIMARY KEY,
  activity_id UUID REFERENCES activities(id),
  student_profile_id UUID REFERENCES student_profiles(id),
  version_number INTEGER,
  generated_output JSONB,
  modalities JSONB,
  status TEXT,
  feedback TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### Tabela: validations

```sql
CREATE TABLE validations (
  id UUID PRIMARY KEY,
  activity_version_id UUID REFERENCES activity_versions(id),
  clarity_score INTEGER,
  accessibility_score INTEGER,
  pedagogical_score INTEGER,
  difficulty_score INTEGER,
  audio_score INTEGER,
  visual_score INTEGER,
  print_score INTEGER,
  approved BOOLEAN,
  rejection_reasons JSONB,
  reviewer_notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### Tabela: files

```sql
CREATE TABLE files (
  id UUID PRIMARY KEY,
  activity_id UUID REFERENCES activities(id),
  activity_version_id UUID REFERENCES activity_versions(id),
  file_type TEXT,
  storage_path TEXT,
  mime_type TEXT,
  original_filename TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

### Tabela: integrations

```sql
CREATE TABLE integrations (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL,
  config JSONB,
  status TEXT DEFAULT 'inactive',
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 24. API Inicial

### Atividades

```text
GET    /activities
POST   /activities
GET    /activities/:id
PUT    /activities/:id
DELETE /activities/:id
```

### Perfis de aluno

```text
GET    /student-profiles
POST   /student-profiles
GET    /student-profiles/:id
PUT    /student-profiles/:id
DELETE /student-profiles/:id
```

### Processamento

```text
POST /activities/:id/process
POST /activities/:id/reprocess
GET  /activities/:id/versions
GET  /activity-versions/:id
```

### Validação

```text
POST /activity-versions/:id/validate
POST /activity-versions/:id/approve
POST /activity-versions/:id/reject
```

### Exportação

```text
GET  /activity-versions/:id/export/pdf
GET  /activity-versions/:id/export/json
GET  /activity-versions/:id/export/html
POST /activity-versions/:id/export/package
```

### Integrações

```text
GET  /integrations
POST /integrations
POST /integrations/:id/test
POST /integrations/:id/import
POST /integrations/:id/export
```

---

## 25. Prompts Modularizados

Os prompts devem ficar separados por responsabilidade.

### Prompt de adaptação cognitiva

Arquivo:

```text
/packages/prompts/adaptation/adapt-cognitive.prompt.md
```

Responsável por:

* Simplificar enunciado.
* Adaptar linguagem.
* Reduzir carga cognitiva.
* Criar instruções por etapa.
* Preservar objetivo pedagógico.

---

### Prompt de geração de áudio

Arquivo:

```text
/packages/prompts/audio/generate-audio.prompt.md
```

Responsável por:

* Criar roteiro de narração.
* Definir pausas.
* Definir tom de voz.
* Separar instruções.
* Gerar versão TTS.

---

### Prompt de geração de imagem

Arquivo:

```text
/packages/prompts/image/generate-activity-image.prompt.md
```

Responsável por:

* Criar prompts de imagens.
* Definir estilo visual.
* Evitar poluição visual.
* Criar pictogramas.
* Criar elementos para cartões.

---

### Prompt de layout de impressão

Arquivo:

```text
/packages/prompts/image/generate-print-layout.prompt.md
```

Responsável por:

* Criar estrutura da folha.
* Definir espaçamentos.
* Definir hierarquia visual.
* Definir áreas de resposta.
* Adaptar para A4.

---

### Prompt de validação

Arquivo:

```text
/packages/prompts/validation/validate-activity.prompt.md
```

Responsável por:

* Avaliar clareza.
* Avaliar dificuldade.
* Avaliar acessibilidade.
* Avaliar preservação pedagógica.
* Avaliar adequação ao perfil.
* Retornar score e motivos.

---

## 26. Exemplo de Fluxo Completo

### Entrada

Professor cadastra:

```text
Título: Animais e Ambientes
Disciplina: Ciências
Ano: 2º ano
Atividade: Classifique os animais em terrestres e aquáticos.
Resposta esperada: Peixe e golfinho são aquáticos. Cachorro e gato são terrestres.
Tipo: Associação
```

Seleciona perfil:

```text
Perfil TEA - apoio visual e frases curtas
```

---

### Processamento

O orquestrador aciona:

```text
1. Leitor de atividade
2. Classificador pedagógico
3. Agente de perfil
4. Adaptador cognitivo
5. Gerador de modalidade visual
6. Gerador de modalidade arrastar e soltar
7. Gerador de impressão
8. Validador
```

---

### Saída

```json
{
  "titulo": "ONDE O ANIMAL VIVE?",
  "instrucoes": [
    "OBSERVE OS ANIMAIS.",
    "COLOQUE CADA ANIMAL NO LUGAR CERTO."
  ],
  "modalidades": {
    "visual": {
      "tipo": "cartoes",
      "itens": ["peixe", "golfinho", "cachorro", "gato"],
      "categorias": ["água", "terra"]
    },
    "interativa": {
      "tipo": "drag_and_drop",
      "itens_arrastaveis": ["peixe", "golfinho", "cachorro", "gato"],
      "zonas_destino": ["água", "terra"]
    },
    "impressao": {
      "formato": "A4",
      "layout": "duas colunas",
      "instrucoes": "LIGUE CADA ANIMAL AO LUGAR ONDE ELE VIVE."
    }
  },
  "validacao": {
    "clareza": 5,
    "acessibilidade": 5,
    "preserva_objetivo": 5,
    "aprovada": true
  }
}
```

---

## 27. Requisitos do MVP

### MVP 1

O primeiro MVP deve conter:

* Tela principal com lista de atividades.
* Cadastro de atividade.
* Cadastro de perfil de aluno.
* Processamento de atividade com IA.
* Geração de pelo menos 3 modalidades:

  * texto adaptado;
  * visual;
  * impressão.
* Validação automática.
* Aprovação/reprovação manual.
* Reprocessamento com feedback.
* Exportação em PDF.
* Docker Compose completo.
* Banco PostgreSQL.
* Storage interno.
* Prompts modularizados.

---

## 28. Requisitos Pós-MVP

Após o MVP, adicionar:

* Áudio gerado por TTS.
* Atividades interativas reais.
* Integração com AI Brain.
* Importação por API.
* n8n para automações.
* MCP para ferramentas externas.
* Dashboard de qualidade.
* Busca semântica no golden dataset.
* Comparação entre versões.
* Multiusuário.
* Permissões por escola.
* Histórico por professor.

---

## 29. Princípios de Design

A interface deve ser:

* Clara.
* Amigável.
* Acessível.
* Leve.
* Colorida com moderação.
* Infantil sem ser exagerada.
* Organizada em cards.
* Fácil para professor usar.
* Fácil de revisar.
* Fácil de imprimir.

Evitar:

* Interface técnica demais.
* Muitas opções na primeira tela.
* Excesso de texto.
* Excesso de cores.
* Fluxos longos.
* Dependência de configuração avançada no MVP.

---

## 30. Princípios Técnicos

O sistema deve ser:

* Modular.
* Dockerizado.
* Integrável.
* API-first.
* Auditável.
* Versionável.
* Rastreável.
* Preparado para reprocessamento.
* Preparado para múltiplas modalidades.
* Preparado para golden dataset.
* Preparado para MCP no futuro.

---

## 31. Prioridade de Desenvolvimento

### Etapa 1

```text
Criar estrutura Docker
Criar banco
Criar backend
Criar frontend
Criar cadastro de atividades
Criar cadastro de perfis
```

### Etapa 2

```text
Criar pipeline de agentes
Criar prompts modularizados
Criar geração de atividade adaptada
Criar geração de modalidade visual
Criar geração de impressão
```

### Etapa 3

```text
Criar validação
Criar aprovação/reprovação
Criar reprocessamento com feedback
Criar histórico de versões
```

### Etapa 4

```text
Criar exportação PDF
Criar storage de arquivos
Criar golden dataset inicial
Criar logs de execução
```

### Etapa 5

```text
Criar integrações externas
Criar n8n
Criar busca semântica
Criar MCP
Criar dashboard
```

---

## 32. Decisão Arquitetural Inicial

A primeira versão deve ser um app web interno rodando em Docker.

Não será um app para download.

A arquitetura deve nascer API-first para permitir integração futura com:

* AI Brain.
* n8n.
* bancos externos.
* APIs educacionais.
* MCP.
* sistemas escolares.

O foco inicial não é criar muitas integrações, mas criar um núcleo sólido:

```text
atividade → perfil → adaptação → modalidade → validação → exportação
```

---

## 33. Resumo do Sistema

O EduAdapt IA será uma plataforma para transformar atividades escolares em atividades multimodais adaptadas.

O sistema parte de uma atividade normal, entende seu objetivo pedagógico, cruza essa informação com um perfil de aluno, gera diferentes modalidades de aplicação e valida se a adaptação ficou adequada.

A atividade pode ser aprovada, reprovada, reprocessada e exportada.

A base de atividades aprovadas forma um golden dataset que melhora a consistência do sistema ao longo do tempo.

A arquitetura deve ser modular, dockerizada, integrável e preparada para agentes, n8n, MCP e bancos externos.

---

## 34. Frase Norteadora

```text
Transformar uma atividade escolar comum em múltiplas experiências pedagógicas acessíveis, adaptadas ao perfil de cada aluno e validadas por critérios educacionais claros.
```
