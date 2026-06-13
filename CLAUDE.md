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
- **IA**: OpenAI gpt-4o-mini (texto) + DALL-E 2 (imagens)

## Docker (local dev)

- Web roda com `npm run dev` (hot-reload via volume mount)
- **NÃO usar** `npm run build && npm start` no Dockerfile — quebra o volume mount do docker-compose
- Para rebuild: `docker compose build web && docker compose up -d web`

## Erros conhecidos

- `next.config.ts` → usar `.js` (TypeScript config não compatível com versão atual)
- `bcrypt==3.2.2` — não atualizar, versões mais novas quebram no Alpine
