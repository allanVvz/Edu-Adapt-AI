# EduAdapt AI — Regras para o Claude Code

## Regra de Branch — OBRIGATÓRIO

**NUNCA commitar diretamente na `main`.**

Todo desenvolvimento deve:
1. Ocorrer em branch `dev` (ou feature branch `feat/<nome>`)
2. Ser commitado e pushed para essa branch
3. Gerar um PR para revisão e aprovação do Allan antes de merge na `main`

```bash
# Fluxo correto
git checkout dev           # ou git checkout -b feat/nome-da-feature
# ... faz as mudanças ...
git add <arquivos>
git commit -m "feat: descrição"
git push origin dev
# Então abrir PR via gh pr create
```

## Commits

- Commitar por pacote de funcionalidade (não tudo de uma vez)
- Mensagens no formato `feat:`, `fix:`, `refactor:`, `test:`, `chore:`
- Sempre incluir `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`

## Stack

- **Frontend**: Next.js 14 (App Router) em `apps/web`
- **Backend**: FastAPI em `apps/api`
- **Banco**: PostgreSQL + pgvector via Docker
- **IA**: OpenAI gpt-4o-mini (texto) + gpt-image-1 (imagens)

## Docker (local dev)

- Web roda com `npm run dev` (hot-reload via volume mount)
- **NÃO usar** `npm run build && npm start` no Dockerfile — quebra o volume mount do docker-compose
- Para rebuild: `docker compose build web && docker compose up -d web`

## Erros conhecidos

- `next.config.ts` → usar `.js` (TypeScript config não compatível com versão atual)
- `bcrypt==3.2.2` — não atualizar, versões mais novas quebram no Alpine
- `openai>=1.75.0` — versão mínima obrigatória; versões antigas não suportam `gpt-image-1`
- **Modelos de imagem**: `dall-e-2` depreciado Nov 2024, `dall-e-3` removido 2025; apenas `gpt-image-1` está em `VALID_IMAGE_MODELS`
- Após mudar `requirements.txt`: rebuild obrigatório → `docker compose build api && docker compose up -d api`
- **Fallback silencioso**: se a chamada OpenAI falha, `generate_adaptation_with_ai` cai no pipeline mock e sinaliza via `output["_fallback"] = True`; `activities.py` usa esse flag para setar `generated_by = "mock"` corretamente

## Regra de negócio: Adaptações por Perfil

- Adaptações pertencem ao **perfil** (`student_profile_id`), não ao aluno
- Todos os alunos com o mesmo perfil veem automaticamente as adaptações daquele perfil
- `student_id` existe no modelo como campo legado opcional — NÃO usar em novos fluxos; acesso é dado pelo perfil via `_can_access()` em `student_area.py`
- A rota `PUT /admin/adaptations/{id}/assign` permite setar `student_id` para compatibilidade retroativa; novos fluxos não devem depender disso
- Novos alunos são criados com `profile_id` preenchido; acesso é dado pelo perfil

## Perfis TEA (seed default)

| Perfil | Complexidade | Modificador de imagem |
|---|---|---|
| TEA — Não Verbal | minimal | AAC pictogram B&W |
| TEA — Hipersensibilidade Visual | low_stimulation | Muted/pastel |
| TEA — Apoio Visual e Leitura Inicial | supported | Colorful cartoon |

## Modificador de imagem por perfil

Função `_get_profile_image_modifier(profile_name)` em `openai_service.py`:
- Detecta tipo de perfil pelo nome (case-insensitive, substring match)
- Retorna suffix appendado ao prompt base no momento da geração
- O prompt COMPLETO (base + modifier) é salvo como `generated[style]["prompt_used"]` no output_data

## Emoji como ilustração (emoji_service.py)

- `CONCEPT_EMOJI`: dict com 160+ conceitos educacionais → emoji
- `get_emoji_for_concept(text)`: case-insensitive, longest-key-first (guarda-chuva > chuva)
- `_build_image_option()` em `openai_service.py`: seta `illustration_type: "emoji"` se match
- `POST /adaptations/{id}/generate-images` pula slots emoji — a menos que `force: true`

## Áudio TTS por perfil

`generate_audio_tts(key, tts_script, voice, speed)` em `openai_service.py`:
- Chama `tts-1` via OpenAI SDK, grava MP3 em `/app/static/audio/`
- Retorna URL pública via `GET /static/audio/{filename}`

Configuração de voz/ritmo por perfil (`audio_generator.py`):

| Perfil | Voz | Ritmo | Marcadores no script |
|--------|-----|-------|---------------------|
| TEA — Não Verbal | onyx | 0.62× | `[aguarda toque]` |
| TEA — Hipersensibilidade Visual | nova | 0.80× | `[pausa]`, `[repete]` |
| TEA — Apoio Visual e Leitura Inicial | shimmer | 0.95× | nenhum |
| Padrão | alloy | 1.00× | nenhum |

`tts_script` = `script` com marcadores `[pausa]`/`[repete]`/`[aguarda toque]` removidos.

## Seed de atividades TEA

`apps/api/app/seeds/seed_tea_activities.py` — 25 atividades × 4 versões = 100 adaptações:
- Chamado automaticamente por `initial.py::run()` ao subir o container
- Idempotente: verifica `(title, teacher_id)` antes de inserir
- Versões: `padrao` (sem perfil) · `p1` (Apoio Visual) · `p2` (Hipersensibilidade) · `p3` (Não Verbal)

## Testes E2E de imagem

Para rodar o teste real (chama a API OpenAI de verdade):
```bash
export OPENAI_TEST_API_KEY=sk-...
make test-images-e2e
```
O teste valida que 4 imagens coerentes são geradas (2 image_options + 2 itens de interação).

Para rodar só os testes de perfil (sem API real):
```bash
make test-profiles
```

## Testes E2E de áudio

```bash
export OPENAI_TEST_API_KEY=sk-...
make test-audio-e2e   # Gera MP3 real, valida tamanho > 1000 bytes
make test-audio       # Testes unitários (TTS mocked)
make test-emoji       # Testes de emoji lookup
```
