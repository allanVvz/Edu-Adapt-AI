# Deploy: Backend público com is-a.dev + ngrok

## Arquitetura

```
Usuário
  │
  ▼
Vercel (frontend Next.js)
  │  NEXT_PUBLIC_API_URL=https://eduadapt-api.is-a.dev
  ▼
is-a.dev DNS → CNAME → musicologically-unburned-glennie.ngrok-free.dev
  │
  ▼
ngrok tunnel (na sua máquina ou servidor)
  │
  ▼
http://localhost:8000 (FastAPI + Docker)
  │
  ▼
PostgreSQL (container Docker local)
```

## Pré-requisitos

- Docker Desktop instalado e rodando
- Conta gratuita em [ngrok.com](https://ngrok.com)
- Conta no GitHub (para PR no is-a.dev)
- CLI do ngrok instalado

## Passo 1 — Subir o backend local

```bash
docker compose up -d --build
```

Verificar:
```bash
# Backend saudável?
curl http://localhost:8000/health
# Swagger disponível?
# Abrir: http://localhost:8000/docs
```

## Passo 2 — Configurar o ngrok com static domain

1. Acesse [ngrok.com](https://ngrok.com) → crie conta gratuita
2. No dashboard → **Domains** → **New Domain**
   - Escolha um nome (ex: `eduadapt-api`) → domínio gerado: `musicologically-unburned-glennie.ngrok-free.dev`
   - Cada conta tem direito a **1 domínio estático gratuito**
3. Copie o auth token em **Your Authtoken**
4. Configure o token:
   ```bash
   ngrok config add-authtoken SEU_TOKEN_AQUI
   ```
5. Suba o tunnel:
   ```bash
   ngrok http --domain=musicologically-unburned-glennie.ngrok-free.dev 8000
   ```
   Mantenha esse terminal aberto enquanto quiser o backend acessível.

6. Valide:
   ```bash
   curl https://musicologically-unburned-glennie.ngrok-free.dev/health
   # ou use o script:
   ./scripts/validate-public-api.sh https://musicologically-unburned-glennie.ngrok-free.dev
   ```

## Passo 3 — Registrar is-a.dev

> ⏱️ O PR no is-a.dev leva **1–7 dias** para ser revisado e aprovado.
> Enquanto isso, use `musicologically-unburned-glennie.ngrok-free.dev` diretamente na Vercel.

1. Fork o repositório [is-a-dev/register](https://github.com/is-a-dev/register) no GitHub
2. No seu fork, crie o arquivo `domains/eduadapt-api.json`:
   ```json
   {
     "description": "EduAdapt AI — API pública do backend FastAPI",
     "repo": "https://github.com/allanVvz/Edu-Adapt-AI",
     "owner": {
       "username": "allanVvz",
       "email": "allanulise027@gmail.com"
     },
     "record": {
       "CNAME": "musicologically-unburned-glennie.ngrok-free.dev"
     }
   }
   ```
   (template em `infra/is-a-dev/eduadapt-api.json` neste repositório)
3. Abra um Pull Request para `is-a-dev/register`
4. Após aprovação e merge, `https://eduadapt-api.is-a.dev` estará ativo

## Passo 4 — Configurar o backend para produção

Antes de expor o backend, configure as variáveis de ambiente:

```bash
# No shell onde o Docker roda, ou via arquivo .env na raiz
export CORS_ORIGINS="http://localhost:3000,https://seu-dominio.vercel.app"
export CORS_ORIGIN_REGEX="https://[a-z0-9-]+\.vercel\.app"
export API_BASE_URL="https://musicologically-unburned-glennie.ngrok-free.dev"
# Após is-a.dev ser aprovado:
# export API_BASE_URL="https://eduadapt-api.is-a.dev"

docker compose down && docker compose up -d --build
```

Ou via arquivo `.env` (copiar de `.env.prod.example`).

## Passo 5 — Configurar NEXT_PUBLIC_API_URL na Vercel

1. Acesse o projeto na Vercel → **Settings** → **Environment Variables**
2. Adicione:
   ```
   Nome:  NEXT_PUBLIC_API_URL
   Valor: https://musicologically-unburned-glennie.ngrok-free.dev
   ```
   (após is-a.dev ser aprovado, troque para `https://eduadapt-api.is-a.dev`)
3. Clique em **Save**
4. Vá em **Deployments** → clique nos três pontos do último deploy → **Redeploy**
   - ⚠️ Obrigatório: `NEXT_PUBLIC_*` é baked no bundle em tempo de build

## Passo 6 — Validar o fluxo completo

```bash
# 1. Validar o backend público
./scripts/validate-public-api.sh https://musicologically-unburned-glennie.ngrok-free.dev

# 2. Testar login via curl
curl -X POST https://musicologically-unburned-glennie.ngrok-free.dev/auth/login \
  -d "username=admin@eduadapt.com&password=admin1234" \
  -H "Content-Type: application/x-www-form-urlencoded"

# 3. Abrir o frontend na Vercel e fazer login
```

## Limitações do método gratuito

| Limitação | Impacto |
|---|---|
| Computador desligado → backend offline | Usuários não conseguem acessar |
| ngrok tunnel reiniciado (sem static domain) → URL muda | CNAME is-a.dev fica inválido |
| is-a.dev: processo via PR, 1–7 dias | Subdomínio não é imediato |
| Imagens/áudios gerados: armazenados localmente | Perdidos se container for removido (`docker volume rm`) |
| Sem HTTPS nativo no FastAPI local | ngrok fornece HTTPS na frente |

Para produção estável sem essas limitações, ver `docker-compose.prod.yml` + Railway/Render.

## Troubleshooting CORS

### Sintoma: `Access to XMLHttpRequest blocked by CORS policy`

**Causa mais comum**: `NEXT_PUBLIC_API_URL` não definida na Vercel → fallback para `localhost:8000`.
**Solução**: configurar a variável e fazer redeploy.

### Sintoma: CORS bloqueado mesmo com URL correta

Verificar no backend:
```bash
# Ver config atual
docker compose exec api python -c "from app.config import settings; print('Origins:', settings.cors_origins_list); print('Regex:', settings.cors_origin_regex)"
```

Verificar se a origem do frontend está na lista:
- `http://localhost:3000` → deve estar em `CORS_ORIGINS`
- `https://abc.vercel.app` → deve ser coberta por `CORS_ORIGIN_REGEX`
- `https://eduadapt.vercel.app` → deve estar em `CORS_ORIGINS` (produção)

### Sintoma: ngrok retorna 502

O container Docker pode não estar rodando:
```bash
docker compose ps
docker compose up -d api
```

### Sintoma: `curl: (6) Could not resolve host`

O is-a.dev ainda não propagou. Use a URL ngrok diretamente até o DNS propagar.
DNS propagation checker: https://dnschecker.org → busque `eduadapt-api.is-a.dev` tipo CNAME.
