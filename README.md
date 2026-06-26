# EduAdapt AI

Plataforma multiagente para geração automática de atividades pedagógicas adaptadas a perfis de alunos com TEA (Transtorno do Espectro Autista).

## Visão geral

O professor cadastra uma atividade. O sistema gera até 4 versões da mesma atividade — uma para cada perfil TEA — com texto simplificado, imagens geradas por IA no estilo adequado ao perfil, narração em áudio com ritmo e voz calibrados, e interações adaptadas (múltipla escolha, drag-and-drop, sequenciamento, toque único). Todo o conteúdo passa por um fluxo de revisão antes de ser publicado ao aluno.

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Next.js 14.2 (App Router), React 18, TypeScript, Zustand, TanStack Query |
| Backend | FastAPI 0.111.0, SQLModel 0.0.19, Alembic 1.13.1 |
| Banco | PostgreSQL 16 + pgvector (Docker) |
| IA — texto | OpenAI gpt-4o-mini |
| IA — imagem | OpenAI gpt-image-1 |
| IA — áudio | OpenAI tts-1 |
| Auth | JWT (python-jose), bcrypt 3.2.2 |
| Testes | Pytest (backend), Jest (frontend) |
| Análise | Radon (complexidade ciclomática) |

---

## Início rápido

Guia detalhado para subir localmente com Docker: [`docs/subir-local-docker.md`](docs/subir-local-docker.md)

```bash
# 1. Subir todos os serviços
make up

# 2. (Aguardar ~10s os health checks passarem)

# 3. Verificar status
docker compose ps

# Acesso
# Frontend: http://localhost:3000
# API:      http://localhost:8000
# Docs:     http://localhost:8000/docs
```

> **Hot-reload ativo** — mudanças em `apps/api/` e `apps/web/` refletem sem rebuild.  
> Exceção: mudanças em `requirements.txt` exigem `docker compose build api && docker compose up -d api`.

---

## Credenciais padrão (seed)

| Email | Senha | Role |
|-------|-------|------|
| admin@eduadapt.local | admin123 | admin |
| professor@eduadapt.local | professor123 | teacher |
| lucas@eduadapt.local | aluno123 | student |
| maria@eduadapt.local | aluno123 | student |
| joao@eduadapt.local | aluno123 | student |

---

## Perfis TEA

Três perfis são criados automaticamente no seed e associados aos alunos acima:

| Perfil | Complexidade | Voz TTS | Ritmo | Imagem |
|--------|-------------|---------|-------|--------|
| TEA — Não Verbal | minimal | onyx | 0.62× | AAC pictograma B&W |
| TEA — Hipersensibilidade Visual | low_stimulation | nova | 0.80× | Paleta dessaturada/pastel |
| TEA — Apoio Visual e Leitura Inicial | supported | shimmer | 0.95× | Cartoon colorido amigável |

**Regra de negócio:** adaptações pertencem ao **perfil**, não ao aluno. Todos os alunos com o mesmo perfil acessam automaticamente as mesmas adaptações publicadas.

---

## Atividades seed

O seed carrega **28 atividades** (3 base + 25 TEA validadas) com **100 adaptações** pré-geradas:

| Disciplina | Atividades | Exemplos |
|------------|-----------|---------|
| Português | AT-PORT-01..05 | Interpretar texto, classes gramaticais, ordem de história, sinônimos, descrever cena |
| Matemática | AT-MAT-01..05 | Adição com maçãs, frações, formas geométricas, padrão de cores, dinheiro |
| Ciências | AT-CIE-01..05 | Vivo/não-vivo, partes da planta, cadeia alimentar, estados da água, sentidos |
| História | AT-HIS-01..05 | Linha do tempo, transportes, regras da comunidade, símbolos nacionais, profissões |
| Geografia | AT-GEO-01..05 | Posição, paisagem natural/construída, clima, mapa e legenda, transporte por via |

Cada uma das 25 atividades TEA tem 4 versões: padrão · p1 (Apoio Visual) · p2 (Hipersensibilidade) · p3 (Não Verbal).

---

## Rotas da API

### Auth
```
POST /auth/login          Login (email + senha) → JWT
GET  /auth/me             Dados do usuário logado
```

### Atividades
```
GET  /activities                Listar atividades
POST /activities                Criar atividade
GET  /activities/{id}           Detalhes
PUT  /activities/{id}           Editar
POST /activities/{id}/adapt     Gerar adaptação (IA ou mock)
```

### Adaptações
```
GET  /adaptations                               Listar (limit=100)
GET  /adaptations/{id}                          Detalhes completos
POST /adaptations/{id}/approve                  Aprovar para revisão
POST /adaptations/{id}/reject                   Rejeitar com feedback
POST /adaptations/{id}/publish                  Publicar para alunos
POST /adaptations/{id}/reprocess                Regerar com feedback
POST /adaptations/{id}/generate-images          Gerar imagens (gpt-image-1)
POST /adaptations/{id}/generate-audio           Gerar áudio TTS (tts-1)
POST /adaptations/{id}/regenerate-image         Regenerar imagem com prompt
POST /adaptations/{id}/apply-gallery-image      Usar imagem da galeria
POST /adaptations/{id}/image-style              Mudar estilo ativo
```

### Perfis e Alunos
```
GET/POST /student-profiles                          CRUD de perfis
GET/PUT  /student-profiles/{id}
GET      /student-profiles/{id}/adaptations         Adaptações do perfil
GET/POST /students                                  CRUD de alunos
GET/PUT  /students/{id}
```

### Área do Aluno
```
GET  /student/activities                            Atividades publicadas (por perfil)
GET  /student/activities/{id}                       Acessar atividade
POST /student/activities/{id}/start                 Iniciar tentativa
POST /student/activities/{id}/submit                Submeter resposta
```

### Galeria, Configurações, Admin
```
GET/POST/PUT/DELETE /gallery                        Galeria de imagens
GET/POST/DELETE     /settings/api-keys              Chaves OpenAI do usuário
POST                /settings/api-keys/{id}/test-images    Validar chave
GET/PUT             /settings/me                    Perfil próprio
GET/PUT             /admin/users/{id}               Gerenciar usuários
GET                 /admin/overview                 Árvore completa

GET                 /static/images/{filename}       Imagens geradas (PNG)
GET                 /static/audio/{filename}        Áudio gerado (MP3)
GET                 /health                         Health check
```

---

## Pipeline de geração

```
POST /activities/{id}/adapt     (body: { profile_id?: string })
  │
  ├─ Com chave OpenAI (na conta do professor):
  │   └─ generate_adaptation_with_ai()
  │       ├─ Usa _profile_to_tea_variant(profile) → atributos do perfil (voz, ritmo, n_opções, etc.)
  │       ├─ Constrói prompt kernel: instruções de consistência de cenário + regras TEA
  │       ├─ Chama gpt-4o-mini com response_format: json_object
  │       ├─ Post-processa: adiciona illustration_type (emoji/generated) aos image_options
  │       └─ Se falha: cai em mock silenciosamente (generated_by fica "mock")
  │
  └─ Sem chave (mock):
      └─ orchestrator.py
          ├─ text_adapter.py         — reescreve enunciado por nível de leitura
          ├─ image_generator.py      — define prompts de imagem por estilo
          ├─ audio_generator.py      — script TTS com marcadores [pausa]/[aguarda toque]
          ├─ interaction_generator.py — estrutura drag-drop/MC/sequencing
          └─ adaptation_validator.py — valida e pontua qualidade

# Uma chamada /adapt gera UMA versão (para o perfil selecionado)
# Para gerar as 4 versões, chamar /adapt 4 vezes com profile_id diferentes
# O seed pré-gera as 100 adaptações (25 atividades × 4 perfis)

POST /adaptations/{id}/generate-images   — chama gpt-image-1 por slot
POST /adaptations/{id}/generate-audio    — chama tts-1 por audio_option
```

### Emoji como ilustração

Antes de gerar uma imagem por IA, o sistema verifica se o conceito tem emoji mapeado (`emoji_service.py`). Se sim, define `illustration_type: "emoji"` e pula a chamada à API — a menos que `force: true` seja passado.

```bash
# 160+ conceitos mapeados:
# "alface" → 🥬   "gato" → 🐱   "avião" → ✈️   "guarda-chuva" → ☂️
```

---

## Testes

```bash
# Testes unitários + integração (sem API externa)
make test-api              # Pytest completo da API
make test-audio            # Áudio: scripts, markers, TTS mocked
make test-emoji            # Emoji: lookup, longest-match, skip/force
make test-profiles         # Modificadores de imagem por perfil
make test-images           # Geração de imagens (mocked)
make test-web              # Jest (frontend)

# E2E com OpenAI real (requer chave)
export OPENAI_TEST_API_KEY=sk-...
make test-images-e2e       # Gera 4 imagens reais
make test-audio-e2e        # Gera MP3 real com TTS

# Qualidade de código
make cc                    # Complexidade ciclomática (radon, threshold: C)
make lint                  # Next.js ESLint

# Tudo de uma vez
make test                  # cc + api + web + health
```

---

## Estrutura de diretórios

```
apps/
  api/
    app/
      agents/           orchestrator.py, audio_generator.py, text_adapter.py, ...
      models/           User, Student, Activity, ActivityAdaptation, ...
      routes/           auth, activities, adaptations, students, profiles, ...
      seeds/            initial.py (usuários/perfis), seed_tea_activities.py (25 atividades)
      services/         openai_service.py, emoji_service.py, auth_service.py
      database.py
      main.py
    tests/              test_agents.py, test_audio_generation.py, test_emoji_illustration.py, ...
    requirements.txt
    Dockerfile
    alembic/

  web/
    app/
      (auth)/login
      (admin)/          dashboard, activities, adaptations, student-profiles, students, gallery, ...
      (student)/        student/activities
    components/
    lib/
    Dockerfile

docker-compose.yml
Makefile
CLAUDE.md              Regras obrigatórias para desenvolvimento
```

---

## Variáveis de ambiente

### Backend (`apps/api/.env`)
```env
DATABASE_URL=postgresql://eduadapt:eduadapt@postgres:5432/eduadapt
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
API_BASE_URL=http://localhost:8000
```

### Frontend (`apps/web/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Regras de desenvolvimento

Ver `CLAUDE.md` na raiz para regras completas. Resumo:

- **Nunca commitar na `main`** — usar `dev` ou `feat/<nome>` + PR
- Commits por pacote de funcionalidade: `feat:`, `fix:`, `refactor:`, `test:`, `chore:`
- `bcrypt==3.2.2` — não atualizar (quebra no Alpine)
- `openai>=1.75.0` — mínimo obrigatório para gpt-image-1
- `next.config.js` — não usar `.ts` (incompatível com a versão atual do Next.js)
- Adaptações pertencem ao **perfil**, não ao aluno — não adicionar `student_id` de volta ao fluxo

---

## Status do MVP

| Funcionalidade | Status |
|---------------|--------|
| Auth JWT (admin/teacher/student) | ✅ |
| CRUD atividades, perfis, alunos | ✅ |
| Geração de adaptações (mock + OpenAI) | ✅ |
| Geração de imagens (gpt-image-1, 2 estilos) | ✅ |
| Galeria de imagens | ✅ |
| Geração de áudio TTS (tts-1, voz/ritmo por perfil) | ✅ |
| Emoji como ilustração | ✅ |
| Seed: 25 atividades × 4 perfis = 100 adaptações | ✅ |
| Scoring de tentativas (alunos) | ✅ |
| Testes unitários e de integração | ✅ |
| Criptografia de API keys (AES-256) | ⚠️ armazenadas em texto plano no MVP |
| Testes E2E com OpenAI real | ⚠️ requerem OPENAI_TEST_API_KEY |
