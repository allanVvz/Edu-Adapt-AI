# EduAdapt AI — Revisão Arquitetural & Psicopedagógica

> **Perspectiva dupla:** Engenharia de Software Sênior × Psicologia Educacional  
> **Data:** 2026-06-27 | **Branch:** `feat/tea-profiles-and-profile-based-adaptations`

---

## 1. Visão Geral do Sistema

EduAdapt AI é uma plataforma multiagente para geração automática de atividades pedagógicas adaptadas a perfis de alunos com Transtorno do Espectro Autista (TEA). O professor cria uma atividade uma vez; o sistema gera automaticamente versões diferenciadas por perfil, com texto simplificado, imagens acessíveis, áudio narrado e interações estruturadas.

### Atores e Papéis

| Ator | Role | Responsabilidades |
|------|------|------------------|
| Administrador | `admin` | Gerenciar usuários, vínculos professor↔aluno, visão global |
| Professor | `teacher` | Criar atividades, revisar adaptações, publicar para alunos |
| Aluno | `student` | Acessar atividades publicadas para seu perfil, registrar tentativas |

---

## 2. Fluxo Principal do Sistema

### 2.1 Jornada do Professor

```
┌─────────────────────────────────────────────────────────────────┐
│  PROFESSOR                                                       │
│                                                                  │
│  1. Login → /auth/login                                         │
│     └─ JWT armazenado em cookie (expira em 24h)                 │
│                                                                  │
│  2. Criar Perfil de Aluno → POST /student-profiles              │
│     ├─ Define: nível de leitura, autonomia, dificuldades         │
│     ├─ Configura: modalidades preferidas, recursos a evitar      │
│     └─ complexity: minimal | low_stimulation | supported         │
│                                                                  │
│  3. Cadastrar Aluno → POST /students                            │
│     └─ Vincula aluno ao perfil + cria User (role="student")     │
│                                                                  │
│  4. Criar Atividade → POST /activities                          │
│     ├─ Preenche: título, disciplina, enunciado, questão          │
│     ├─ Define: ano escolar, objetivo pedagógico, habilidade BNCC │
│     └─ Status inicial: "draft"                                   │
│                                                                  │
│  5. Gerar Adaptação → POST /activities/{id}/adapt               │
│     ├─ [Opcional] Seleciona perfil (profile_id)                 │
│     ├─ Pipeline IA: gpt-4o-mini → output_data                   │
│     └─ Status: "review" (aguardando revisão)                     │
│                                                                  │
│  6. Revisar Adaptação → /admin/adaptations/{id}/review          │
│     ├─ Opção A: REJEITAR → feedback → reprocessar               │
│     ├─ Opção B: GERAR IMAGENS → gpt-image-1 por slot            │
│     ├─ Opção C: GERAR ÁUDIO → tts-1 por script                  │
│     └─ Opção D: PUBLICAR → status="published"                   │
│                                                                  │
│  7. Atividade disponível para alunos do perfil                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Jornada do Aluno

```
┌─────────────────────────────────────────────────────────────────┐
│  ALUNO                                                           │
│                                                                  │
│  1. Login → /auth/login                                         │
│     └─ Redireciona para /student                                 │
│                                                                  │
│  2. Ver Atividades → GET /student/activities                    │
│     └─ Lista: adaptation.status="published" AND                  │
│        (student_id == eu OR student_profile_id == meu_perfil)   │
│                                                                  │
│  3. Abrir Atividade → GET /student/activities/{adaptation_id}   │
│     └─ Recebe output_data com URLs normalizadas                  │
│                                                                  │
│  4. Iniciar → POST /student/activities/{id}/start               │
│     └─ Cria StudentActivityAttempt (status="started")            │
│                                                                  │
│  5. Interagir → Interface adaptada ao perfil                     │
│     ├─ Múltipla escolha (large-touch buttons para TEA p3)        │
│     ├─ Drag-and-drop (pictogramas para não-verbal)               │
│     └─ Sequenciamento                                            │
│                                                                  │
│  6. Submeter → POST /student/activities/{id}/submit             │
│     ├─ Calcula score (_calculate_score)                          │
│     └─ Salva tentativa com score/max_score/tempo                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Pipeline de Adaptação (Núcleo do Sistema)

```
POST /activities/{id}/adapt
        │
        ├─ Tem chave OpenAI?
        │       │
        │   SIM └─ generate_adaptation_with_ai()
        │           ├─ Constrói system prompt com regras TEA
        │           ├─ Chama gpt-4o-mini (JSON mode)
        │           ├─ Parseia output_data
        │           └─ Fallback silencioso → mock (set _fallback=True)
        │
        └─ NÃO → run_adaptation_pipeline() [orquestrador mock]
                  ├─ adapt_text()              → simplificação textual
                  ├─ generate_image_options()  → prompts de imagem
                  ├─ generate_audio_options()  → scripts TTS + marcadores
                  ├─ generate_visual_modality()→ hints de layout
                  ├─ generate_interaction()    → estrutura interação
                  ├─ validate_adaptation()     → métricas de qualidade
                  └─ _generate_print_version() → formato A4 imprimível
```

### 2.4 Pipeline de Geração de Imagens

```
POST /adaptations/{id}/generate-images
        │
        ├─ Para cada image_option / interaction_item:
        │   │
        │   ├─ 1. Emoji match? → get_emoji_for_concept(description)
        │   │     └─ SIM → illustration_type="emoji", pula chamada IA
        │   │
        │   ├─ 2. Galeria match? → busca prompt similar no banco
        │   │     └─ SIM → reusa URL existente (economia API)
        │   │
        │   └─ 3. Gera via gpt-image-1
        │         ├─ Aplica _get_profile_image_modifier(profile_name)
        │         ├─ Salva PNG em /app/static/images/
        │         ├─ Registra na GalleryImage
        │         └─ Atualiza slot em output_data
        │
        └─ Retorna: {images_generated, errors[]}
```

### 2.5 Máquina de Estados da Adaptação

```
          ┌──────────┐
          │  draft   │ ← adaptação recém-criada pelo seed / /adapt
          └────┬─────┘
               │ /adapt ou seed
               ▼
          ┌──────────┐
          │  review  │ ← aguarda revisão do professor
          └────┬─────┘
         ┌─────┴──────┐
         │             │
         ▼             ▼
    ┌──────────┐  ┌──────────┐
    │ approved │  │ rejected │
    └────┬─────┘  └────┬─────┘
         │              │ /reprocess (version++)
         │              ▼
         │         ┌──────────┐
         │         │  review  │ ← nova versão gerada
         │         └──────────┘
         ▼
    ┌──────────┐
    │published │ ← visível para alunos
    └──────────┘
```

---

## 3. Arquitetura Técnica

### 3.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────┐
│                        DOCKER COMPOSE                           │
│                                                                  │
│  ┌───────────────┐    ┌───────────────┐    ┌──────────────────┐ │
│  │   Next.js 14  │    │   FastAPI     │    │  PostgreSQL 16   │ │
│  │   (React 18)  │◄──►│   (Python)    │◄──►│  + pgvector      │ │
│  │   :3000       │    │   :8000       │    │  :5432           │ │
│  │               │    │               │    │                  │ │
│  │  App Router   │    │  SQLModel ORM │    │  Alembic         │ │
│  │  Zustand      │    │  JWT Auth     │    │  migrations      │ │
│  │  React Query  │    │  CORS         │    │                  │ │
│  │  Tailwind CSS │    │               │    │                  │ │
│  └───────────────┘    └───────┬───────┘    └──────────────────┘ │
│                               │                                  │
└───────────────────────────────┼──────────────────────────────────┘
                                │ HTTPS
                    ┌───────────▼───────────┐
                    │     OpenAI API        │
                    │  gpt-4o-mini (texto)  │
                    │  gpt-image-1 (imagem) │
                    │  tts-1 (áudio)        │
                    └───────────────────────┘
```

### 3.2 Modelos de Dados — Relacionamentos

```
User (1) ──────────────────── (N) Activity
  │                                  │
  │                                  │ (1)
  │                           ActivityAdaptation (N)
  │                                  │ ├─ student_profile_id (FK)
  │                                  │ └─ student_id (FK, legado)
  │                                  │
  ├── (1) Student (N) ───────────────┘
  │          │
  │          └── profile_id → StudentProfile
  │
  └── (N) TeacherStudent (N) ── Student
             │
             └─ junction table teacher↔student
```

### 3.3 Perfis TEA e Modificadores

| Perfil | Complexidade | Voz TTS | Ritmo | Modificador de Imagem |
|--------|-------------|---------|-------|----------------------|
| TEA — Não Verbal | minimal | onyx | 0.62× | AAC pictogram B&W, thick outline |
| TEA — Hipersensibilidade Visual | low_stimulation | nova | 0.80× | Muted/pastel, clean composition |
| TEA — Apoio Visual e Leitura Inicial | supported | shimmer | 0.95× | Colorful cartoon, child-friendly |
| Padrão (sem perfil) | — | alloy | 1.00× | — |

---

## 4. Acertos do Projeto

### 4.1 Arquitetura

- **Profile-based access é a decisão certa.** Desacopla adaptação de aluno específico: todos com o mesmo perfil recebem automaticamente as atividades daquele perfil. Escalável para turmas inteiras.
- **Fallback silencioso bem implementado.** `_fallback=True` + `generated_by="mock"` dão rastreabilidade sem quebrar o fluxo do professor em ambientes sem chave OpenAI.
- **Seed idempotente.** Verificação por `(title, teacher_id)` permite rebuilds do container sem duplicação de dados.
- **Galeria de imagens como cache.** Reusar imagens de prompts similares é economicamente inteligente — reduz chamadas API e acelera geração para atividades com conceitos recorrentes.
- **Emoji como ilustração de baixo custo.** 160+ conceitos mapeados: evita chamar gpt-image-1 para conceitos simples e universais (ex: "banana" → 🍌).
- **Scoring com crédito parcial.** Drag-and-drop aceita respostas parcialmente corretas — pedagogicamente correto para alunos TEA que podem ter dificuldades motoras, não cognitivas.
- **Marcadores de áudio por perfil.** `[pausa]`/`[repete]`/`[aguarda toque]` removidos do script TTS mas presentes no roteiro do professor — detalhe de experiência que demonstra cuidado com TEA.

### 4.2 Psicopedagógico

- **Perfis fundamentados em critérios reais.** `reading_level`, `autonomy_level`, `preferred_modalities`, `resources_to_avoid` espelham categorias usadas em laudos e planos de AEE (Atendimento Educacional Especializado).
- **Habilidades BNCC no modelo.** Campo `bncc_skill` permite alinhamento curricular formal — crítico para justificativa pedagógica com gestores e famílias.
- **Interação por toque.** Tipo `"toque"` mapeado como `multiple_choice` com botões grandes — considero intervenção acessível para alunos com hipersensibilidade motora fina.
- **Ritmo de áudio diferenciado.** Reduzir para 0.62× (TEA Não Verbal) é clinicamente embasado: processamento auditivo mais lento é documentado em pesquisas de TEA de nível de suporte mais alto.
- **Separação `script` vs. `tts_script`.** O professor vê o roteiro completo com marcadores pedagógicos; o TTS recebe a versão limpa. Demonstra entendimento de que a anotação pedagógica não é para a máquina.

---

## 5. Erros e Riscos Identificados

### 5.1 Críticos (produção bloqueada)

#### ERR-01 — API Key armazenada em texto claro
**Localização:** `apps/api/app/models/api_key.py` (`encrypted_value: str`)  
**Risco:** Chave OpenAI do professor exposta em qualquer dump de banco de dados.  
**Impacto:** Faturamento de terceiros, vazamento de dados de atividades escolares.  
**Solução:** AES-256-GCM com chave derivada de `SECRET_KEY` + rotação de envelope key. Mínimo aceitável: Fernet (cryptography lib).

#### ERR-02 — SECRET_KEY hardcoded no docker-compose
**Localização:** `docker-compose.yml` → `SECRET_KEY: dev-secret-key-change-in-production`  
**Risco:** JWT forjável se este compose for usado em produção.  
**Impacto:** Qualquer usuário pode gerar token admin válido.  
**Solução:** Variável obrigatória sem default; validação no boot com `assert settings.secret_key != "dev-secret-key-change-in-production"`.

#### ERR-03 — Fallback silencioso sem notificação ao professor
**Localização:** `apps/api/app/services/openai_service.py` → `output["_fallback"] = True`  
**Risco:** Professor recebe adaptação mock sem saber que a IA falhou. Qualidade degradada sem aviso.  
**Impacto:** Adaptações inadequadas publicadas para alunos TEA.  
**Solução:** Retornar campo `generated_by: "mock"` com aviso explícito na UI de revisão: "⚠️ Esta adaptação foi gerada sem IA — revise com atenção antes de publicar."

### 5.2 Altos (impedem uso real em escola)

#### ERR-04 — Sem limite de tentativas no submit
**Localização:** `apps/api/app/routes/student_area.py`  
**Risco:** Aluno pode submeter a mesma atividade infinitamente, inflando métricas de score.  
**Impacto psicopedagógico:** Dados de desempenho não confiáveis; professor não consegue avaliar evolução real.  
**Solução:** Limite configurável por perfil (ex: 3 tentativas para TEA Apoio Visual, ilimitado para TEA Não Verbal em fase de familiarização).

#### ERR-05 — Scoring ignora tentativas anteriores
**Localização:** `_calculate_score()` em `student_area.py:47-77`  
**Risco:** Cada submissão é tratada isoladamente — sistema não calcula evolução, não detecta regressão.  
**Impacto psicopedagógico:** Impossível gerar relatório de progresso para AEE ou para família.  
**Solução:** Agregar `StudentActivityAttempt` por `student_id + adaptation_id` para calcular: melhor score, média, número de tentativas, tempo médio.

#### ERR-06 — `student_id` legado coexiste com `student_profile_id` sem validação
**Localização:** `apps/api/app/models/adaptation.py`  
**Risco:** Adaptação pode ter ambos preenchidos com inconsistência (ex: student_id de um aluno de perfil diferente de student_profile_id).  
**Solução:** Constraint de banco ou validação Pydantic: `CHECK (student_id IS NULL OR student_profile_id IS NULL OR student.profile_id == student_profile_id)`.

#### ERR-07 — Versioning de adaptação não versiona output_data
**Localização:** `POST /adaptations/{id}/reprocess`  
**Risco:** Versão anterior é perdida quando nova versão é gerada — histórico não existe.  
**Impacto:** Professor não pode comparar versão 1 vs. versão 2 para entender o que mudou.  
**Solução:** Salvar snapshot de `output_data` anterior antes de reprocessar, ou criar `AdaptationVersion` como tabela separada.

### 5.3 Médios (degradam experiência)

#### ERR-08 — Ausência de timeout nas chamadas OpenAI
**Localização:** `openai_service.py` → `make_openai_client()`  
**Risco:** Chamada gpt-4o-mini pode travar por minutos sem responder.  
**Impacto:** Professor fica na tela de loading indefinidamente.  
**Solução:** `timeout=httpx.Timeout(30.0, connect=5.0)` no construtor AsyncOpenAI.

#### ERR-09 — Geração de imagens é síncrona e bloqueia a requisição
**Localização:** `POST /adaptations/{id}/generate-images` (400+ linhas síncronas)  
**Risco:** Adaptações com 4+ imagens podem levar 60-90s, causando timeout de 502 em proxies.  
**Solução:** Fila assíncrona (Celery/RQ) + polling de status, ou ao menos `asyncio.gather` para gerar slots em paralelo.

#### ERR-10 — Imagens servidas sem cache-control
**Localização:** `GET /static/images/{filename}` em `main.py`  
**Risco:** Cada carregamento de atividade pelo aluno refaz o request ao servidor.  
**Impacto:** Lentidão em escolas com conexão fraca (realidade brasileira).  
**Solução:** `Cache-Control: max-age=31536000, immutable` (imagens geradas não mudam).

#### ERR-11 — Sem paginação em `GET /student/activities`
**Localização:** `apps/api/app/routes/student_area.py`  
**Risco:** Com 100 adaptações de seed + adaptações futuras, retorna tudo sem limite.  
**Solução:** `limit=20, offset=0` como padrão, com metadados de paginação no response.

### 5.4 Psicopedagógicos

#### ERR-P01 — Perfis TEA são fixos no seed; professor não pode customizar
**Risco:** Alunos TEA são heterogêneos — dois alunos com mesmo diagnóstico podem ter necessidades opostas.  
**Impacto:** Professor é forçado a usar um dos 3 perfis padrão mesmo que não seja ideal.  
**Solução:** Os perfis já existem como entidade editável (`PUT /student-profiles/{id}`) — garantir que a UI exponha edição completa dos campos de acessibilidade, não apenas nome e descrição.

#### ERR-P02 — Sem módulo de observação do professor durante tentativa
**Risco:** Professor não sabe se aluno travou, desistiu ou está progredindo.  
**Impacto:** Impossível suporte em tempo real ou diagnóstico de dificuldade específica.  
**Solução:** Salvar eventos intermediários (ex: `{"event": "item_moved", "slot": "A", "timestamp": ...}`) em `raw_response` durante a sessão, antes do submit.

#### ERR-P03 — Feedback de score é binário (percentual) sem orientação
**Risco:** Um aluno TEA que recebe "40%" não sabe o que errou ou como tentar de novo.  
**Solução:** Gerar mensagem de feedback contextualizada por perfil após submit (ex: para TEA Não Verbal: pictograma de "tente de novo" + som; para TEA Apoio Visual: frase curta + imagem do item correto).

---

## 6. Possibilidades de Melhoria

### 6.1 Curto Prazo (próximo sprint)

| Prioridade | Melhoria | Esforço |
|-----------|----------|---------|
| 🔴 Alta | Criptografar API keys com Fernet | 4h |
| 🔴 Alta | Aviso explícito de fallback mock na UI | 2h |
| 🟡 Média | Timeout nas chamadas OpenAI | 1h |
| 🟡 Média | Cache-Control para arquivos estáticos | 1h |
| 🟡 Média | Limite de tentativas configurável por perfil | 6h |
| 🟢 Baixa | Paginação em `GET /student/activities` | 2h |

### 6.2 Médio Prazo (1-2 meses)

#### M01 — Dashboard de Progresso do Aluno
Agregar `StudentActivityAttempt` para exibir:
- Evolução temporal de score (linha do tempo)
- Habilidades BNCC trabalhadas vs. dominadas
- Comparação entre tentativas de uma mesma atividade
- Tempo médio de conclusão por tipo de interação

**Por que isso importa psicopedagogicamente:** Relatórios de evolução são obrigatórios em planos de AEE e justificam continuidade de metodologias para famílias e gestores.

#### M02 — Modo de Apresentação Adaptado por Perfil
Em vez de renderizar a mesma página com dados diferentes, criar componentes de player específicos por perfil:

- **TEA Não Verbal:** Tela dividida 1/3 instrução + 2/3 interação, pictogramas AAC nas instruções, botão único "PRONTO" com símbolo
- **TEA Hipersensibilidade Visual:** Fundo cinza-claro, no máximo 1 elemento animado, transições desabilitadas, sem notificações sonoras inesperadas
- **TEA Apoio Visual:** Cards coloridos com borda arredondada, instrução em áudio automático ao abrir, feedback imediato por item

#### M03 — Histórico de Versões de Adaptação
Antes do `/reprocess`, snapshottear `output_data` + `validator_feedback` em tabela `adaptation_versions`. Interface de diff lado a lado para o professor comparar versões.

#### M04 — Geração de Imagens Assíncrona
Fila com RQ (Redis Queue) ou Celery:
```
POST /adaptations/{id}/generate-images → {job_id}
GET  /adaptations/{id}/image-job/{job_id} → {status, progress, errors}
```
Frontend faz polling ou usa WebSocket para atualização em tempo real.

#### M05 — Galeria de Símbolos AAC Curada
Substituir emojis Unicode por símbolos AAC reais (ex: Boardmaker, ARASAAC — licença livre) para o perfil TEA Não Verbal. Emojis são universais mas não são o padrão clínico de comunicação aumentativa.

### 6.3 Longo Prazo (3-6 meses)

#### L01 — Personalização Dinâmica por Tentativa
Após N tentativas com score < 50%, o sistema sugere automaticamente:
- Reduzir complexidade da interação (de drag-and-drop para múltipla escolha)
- Adicionar dica visual (seta para zona correta)
- Reduzir número de alternativas (3 → 2)

Isso requer um agente de adaptação reativa separado do pipeline atual.

#### L02 — Laudo Digital Integrado
Importar dados estruturados de laudos (PDF ou formulário) para popular campos de `StudentProfile` automaticamente, reduzindo trabalho manual do professor e garantindo fidelidade ao diagnóstico clínico.

#### L03 — Relatório para Família
Geração automática de PDF mensal com: atividades realizadas, habilidades trabalhadas, evolução de score, observações do professor — em linguagem acessível (sem jargão técnico).

#### L04 — Suporte Multi-Idioma / LIBRAS
Adicionar opção de instrução em LIBRAS (vídeo ou avatar 3D) para alunos surdos + TEA, que é uma combinação de necessidades presente em escolas de educação especial.

#### L05 — pgvector em uso real
O banco já tem pgvector instalado mas não utilizado. Usar embeddings de `output_data.text_adaptations` para:
- Detectar atividades duplicadas antes de inserir
- Busca semântica na galeria ("encontre imagens de animais de fazenda")
- Sugestão de atividades similares ao professor

---

## 7. Resumo Executivo

### O que funciona bem

O núcleo técnico está sólido: pipeline de adaptação com fallback, galeria de imagens como cache, emojis como otimização, seed idempotente, e a decisão arquitetural mais importante — **acesso por perfil em vez de por aluno** — é escalável e pedagogicamente correto.

Os 3 perfis TEA no seed são adequados como ponto de partida. A diferenciação de voz/ritmo de áudio por perfil e os modificadores de imagem demonstram que houve pesquisa real de literatura sobre TEA.

### O que bloqueia produção

1. API keys em texto claro (risco de segurança imediato)
2. Fallback silencioso sem aviso (risco pedagógico)
3. Sem histórico de progresso do aluno (inviabiliza uso em AEE real)
4. Geração de imagens síncrona (timeout em uso real com imagens múltiplas)

### Prioridade de desenvolvimento

```
IMEDIATO    → ERR-01 (criptografia) + ERR-03 (aviso fallback)
ANTES DA    → ERR-04 (limite tentativas) + ERR-05 (progresso aluno)
ESCOLA      → M01 (dashboard progresso) + M02 (player por perfil)
PÓS-PILOTO  → M03 a M05, L01 a L04
```

---

*Documento gerado em colaboração entre perspectiva de Engenharia de Software Sênior e Psicologia Educacional aplicada ao contexto TEA no Brasil.*  
*Referências pedagógicas: AEE (Resolução CNE/CEB 4/2009), BNCC, protocolo ARASAAC (AAC), DSM-5 critérios TEA.*
