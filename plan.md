# EduAdapt AI — Plano Técnico de Execução

## 1. Resumo dos Documentos Existentes

### Sistema Multiagente para Atividades Multimodais Adaptadas
Documento de 34 seções descrevendo a visão completa do sistema:
- **Propósito:** transformar atividades escolares comuns em versões multimodais adaptadas ao perfil pedagógico de cada aluno
- **Pipeline multiagente:** Orquestrador → Leitor → Classificador Pedagógico → Perfil do Aluno → Adaptador Cognitivo → Gerador de Modalidades → Áudio → Imagem/Layout → Interação → Validador → Revisão Humana → Exportação
- **Modalidades de saída:** texto adaptado, visual, áudio, arrastar/soltar, impressão, brincadeira
- **Golden Dataset:** base de atividades aprovadas para benchmark e melhoria contínua
- **Stack definida:** Next.js + FastAPI + PostgreSQL + pgvector + MinIO + Redis + Celery + Docker

### Soluções, Modelos e Agentes de IA para Atividades Adaptadas
Documento de pesquisa sobre soluções existentes no mercado:
- Agente Adapton Educa (Professor Alberto) — prompt estruturado para TEA/DI com Currículo Paulista
- ChatGPT com "Prompt Mágico" (Prof. Julio Passos) — simplificação de linguagem
- Livox — CAAA para alunos não verbais
- Modelos de prompt prontos para simplificação, apoio visual, geração de folha A4

---

## 2. Arquitetura Encontrada no Projeto

**Estado atual:** repositório vazio, apenas os dois documentos conceituais.

**Arquitetura alvo:**
```
Browser (Next.js) ←→ FastAPI ←→ PostgreSQL
                          ↓
                    Agents Layer (mock → OpenAI)
                          ↓
                    Prompts Package (modular)
```

Separação por roles:
- `admin` e `teacher` → painel administrativo completo
- `student` → área do aluno isolada

---

## 3. Stack Atual Detectada

Repositório sem código. Stack a criar do zero conforme briefing:

| Camada | Tecnologia |
|--------|-----------|
| Frontend | Next.js 14 + TypeScript + Tailwind CSS |
| Backend | FastAPI + Python 3.11 |
| ORM | SQLModel (SQLAlchemy + Pydantic) |
| Migrations | Alembic |
| Auth | JWT (python-jose + passlib) |
| Banco | PostgreSQL 16 (pgvector/pgvector:pg16) |
| Container | Docker Compose |
| Storage (futuro) | MinIO |
| Workers (futuro) | Redis + Celery |
| IA | OpenAI API (chave por professor) |
| Deploy (futuro) | Vercel frontend + Docker API/VPS |

---

## 4. Estrutura de Pastas Atual

```
eduadapt-ai/  (vazio)
├── Sistema Multiagente...md
└── Soluções, Modelos...md
```

---

## 5. Plano de Implementação em Fases

### Fase 1 — Infraestrutura e Base
- Docker Compose (api + web + postgres)
- Backend FastAPI estruturado
- Conexão com PostgreSQL
- Migrations Alembic
- Seeds iniciais
- Auth JWT

### Fase 2 — Frontend e Layouts por Role
- Next.js base com Tailwind
- Layout professor vs. aluno
- Login
- Dropdown de usuário
- Redirecionamento por role

### Fase 3 — Gestão
- Settings (/settings)
- API Keys (/settings/api-keys)
- CRUD alunos (/students)
- Perfis pedagógicos (/student-profiles)
- CRUD atividades (/activities)

### Fase 4 — Adaptação
- Estrutura modular de agentes
- Prompts separados por modalidade
- Geração mockada
- Revisão com abas
- Aprovação/publicação

### Fase 5 — Área do Aluno
- /student
- Execução de atividade
- Registro de tentativa e nota

### Fase 6 — Dashboard e Documentação
- Dashboard do professor
- docs/vercel-mcp.md
- /settings/integrations (mock)

---

## 6. Arquivos que Serão Criados

### Infraestrutura
```
docker-compose.yml
.env.example
.gitignore
apps/api/Dockerfile
apps/web/Dockerfile
```

### Backend
```
apps/api/requirements.txt
apps/api/alembic.ini
apps/api/alembic/env.py
apps/api/alembic/versions/001_initial.py
apps/api/app/__init__.py
apps/api/app/main.py
apps/api/app/config.py
apps/api/app/database.py
apps/api/app/models/__init__.py
apps/api/app/models/user.py
apps/api/app/models/teacher.py
apps/api/app/models/student.py
apps/api/app/models/student_profile.py
apps/api/app/models/activity.py
apps/api/app/models/adaptation.py
apps/api/app/models/attempt.py
apps/api/app/models/api_key.py
apps/api/app/models/agent_run.py
apps/api/app/routes/__init__.py
apps/api/app/routes/auth.py
apps/api/app/routes/settings.py
apps/api/app/routes/students.py
apps/api/app/routes/profiles.py
apps/api/app/routes/activities.py
apps/api/app/routes/adaptations.py
apps/api/app/routes/student_area.py
apps/api/app/routes/dashboard.py
apps/api/app/services/__init__.py
apps/api/app/services/auth_service.py
apps/api/app/services/openai_service.py
apps/api/app/agents/__init__.py
apps/api/app/agents/orchestrator.py
apps/api/app/agents/text_adapter.py
apps/api/app/agents/audio_generator.py
apps/api/app/agents/image_generator.py
apps/api/app/agents/visual_modality_generator.py
apps/api/app/agents/interaction_generator.py
apps/api/app/agents/adaptation_validator.py
apps/api/app/seeds/__init__.py
apps/api/app/seeds/initial.py
```

### Prompts
```
packages/prompts/text/text-adaptation.prompt.md
packages/prompts/audio/audio-generation.prompt.md
packages/prompts/image/image-illustration.prompt.md
packages/prompts/visual/visual-activity.prompt.md
packages/prompts/interaction/drag-drop.prompt.md
packages/prompts/validation/adaptation-validation.prompt.md
```

### Frontend
```
apps/web/package.json
apps/web/tsconfig.json
apps/web/tailwind.config.ts
apps/web/next.config.ts
apps/web/app/layout.tsx
apps/web/app/page.tsx
apps/web/app/(auth)/login/page.tsx
apps/web/app/(admin)/dashboard/page.tsx
apps/web/app/(admin)/settings/page.tsx
apps/web/app/(admin)/settings/api-keys/page.tsx
apps/web/app/(admin)/settings/integrations/page.tsx
apps/web/app/(admin)/students/page.tsx
apps/web/app/(admin)/student-profiles/page.tsx
apps/web/app/(admin)/activities/page.tsx
apps/web/app/(admin)/adaptations/[id]/review/page.tsx
apps/web/app/(student)/student/page.tsx
apps/web/app/(student)/student/activities/[id]/page.tsx
apps/web/components/layout/AdminLayout.tsx
apps/web/components/layout/StudentLayout.tsx
apps/web/components/layout/UserDropdown.tsx
apps/web/components/ui/ (componentes base)
apps/web/lib/api.ts
apps/web/lib/auth.ts
```

### Documentação
```
docs/vercel-mcp.md
```

---

## 7. Arquivos que Serão Alterados

Nenhum — repositório vazio.

---

## 8. Migrations Necessárias

```sql
-- 001_initial.py (Alembic)
users
teachers
students
student_profiles
teacher_students
activities
activity_adaptations
student_activity_attempts
api_keys
agent_documents
agent_runs
```

---

## 9. Rotas de API Necessárias

### Auth
- `POST /auth/login`
- `GET /auth/me`

### Settings
- `GET /settings/me`
- `PUT /settings/me`
- `GET /settings/api-keys`
- `POST /settings/api-keys`
- `DELETE /settings/api-keys/{id}`

### Students
- `GET /students`
- `POST /students`
- `GET /students/{id}`
- `PUT /students/{id}`

### Profiles
- `GET /student-profiles`
- `POST /student-profiles`
- `GET /student-profiles/{id}`
- `PUT /student-profiles/{id}`

### Activities
- `GET /activities`
- `POST /activities`
- `GET /activities/{id}`
- `PUT /activities/{id}`
- `POST /activities/{id}/adapt`

### Adaptations
- `GET /adaptations/{id}`
- `POST /adaptations/{id}/approve`
- `POST /adaptations/{id}/reject`
- `POST /adaptations/{id}/reprocess`
- `POST /adaptations/{id}/publish`

### Student Area
- `GET /student/activities`
- `GET /student/activities/{adaptation_id}`
- `POST /student/activities/{adaptation_id}/start`
- `POST /student/activities/{adaptation_id}/submit`

### Dashboard
- `GET /dashboard/teacher`

---

## 10. Telas Necessárias

| Rota | Descrição | Role |
|------|-----------|------|
| `/login` | Login com email/senha | público |
| `/dashboard` | Painel principal com cards de métricas | admin/teacher |
| `/activities` | Lista de atividades | admin/teacher |
| `/activities/new` | Criar atividade (modal) | admin/teacher |
| `/adaptations/:id/review` | Revisar adaptação com abas | admin/teacher |
| `/students` | Listar/criar alunos | admin/teacher |
| `/student-profiles` | Perfis pedagógicos | admin/teacher |
| `/settings` | Configurações de conta | todos |
| `/settings/api-keys` | Chaves de API | admin/teacher |
| `/settings/integrations` | Integrações (mock) | admin/teacher |
| `/student` | Área do aluno — lista de atividades | student |
| `/student/activities/:id` | Executar atividade | student |

---

## 11. Fluxo de Teste Manual

```
1. docker compose up --build
2. Aguardar migrations automáticas
3. POST /auth/login {email: "admin@eduadapt.local", password: "admin123"}
4. Verificar token e role=admin
5. GET /students → deve retornar aluno seed
6. GET /activities → deve retornar atividade "Animais e Ambientes"
7. POST /activities/:id/adapt → deve retornar adaptação mockada
8. GET /adaptations/:id → verificar JSON com text_adaptations, image_options, audio_options
9. POST /adaptations/:id/publish
10. POST /auth/login {email: "aluno@eduadapt.local", password: "aluno123"}
11. GET /student/activities → deve retornar a atividade publicada
12. POST /student/activities/:id/submit {response: {...}}
13. GET /dashboard/teacher → verificar métricas
```

---

## 12. Riscos Técnicos

| Risco | Mitigação |
|-------|-----------|
| Windows paths no Docker | Usar apenas forward slashes, volumes com wsl2 backend |
| Alembic com SQLModel | Usar `SQLModel.metadata` no alembic env.py |
| CORS Next.js ↔ FastAPI | Configurar origins corretos no FastAPI |
| JWT expiração | Refresh token não implementado no MVP |
| OpenAI sem chave | Fallback mock obrigatório |
| Segurança API Keys | Armazenar com aviso de criptografia pendente |

---

## 13. Próximos Passos

1. Criar infraestrutura Docker
2. Implementar backend FastAPI completo
3. Implementar frontend Next.js
4. Testar fluxo completo manual
5. Commit por fase para aprovação
6. Integrar OpenAI real após aprovação das fases base
7. Implementar storage MinIO
8. Implementar workers Celery/Redis
9. Golden Dataset
10. Deploy Vercel + VPS via MCP Claude
