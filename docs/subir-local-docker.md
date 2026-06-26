# Subir o EduAdapt AI localmente com Docker

Este projeto esta preparado para rodar via Docker Compose.

O arquivo principal para desenvolvimento local e:

```bash
docker-compose.yml
```

Ele sobe 3 servicos:

| Servico | Funcao | Porta local |
|---|---|---|
| `postgres` | Banco PostgreSQL 16 com pgvector | `5432` |
| `api` | Backend FastAPI | `8000` |
| `web` | Frontend Next.js | `3000` |

## 1. Pre-requisitos

Antes de subir, confirme:

1. Docker Desktop esta aberto e rodando.
2. Voce esta na raiz do projeto:

```powershell
cd C:\Repositores\Edu-Adapt-AI
```

3. O arquivo `.env` existe na raiz.

Neste repositorio ele ja existe. Se precisar recriar:

```powershell
Copy-Item .env.example .env
```

## 2. Subir agora

Na raiz do projeto, rode:

```powershell
docker compose up -d
```

Ou, usando o Makefile:

```powershell
make up
```

Na primeira execucao, o Docker pode demorar porque vai baixar imagens e instalar dependencias.

## 3. Verificar se subiu

Rode:

```powershell
docker compose ps
```

O esperado e ver os servicos `postgres`, `api` e `web` rodando.

Depois acesse:

| Aplicacao | URL |
|---|---|
| Frontend | http://localhost:3000 |
| API | http://localhost:8000 |
| Swagger / Docs da API | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

## 4. Credenciais padrao

O seed roda automaticamente quando a API sobe.

| Perfil | Email | Senha |
|---|---|---|
| Admin | `admin@eduadapt.local` | `admin123` |
| Professor | `professor@eduadapt.local` | `professor123` |
| Aluno Lucas | `lucas@eduadapt.local` | `aluno123` |
| Aluna Maria | `maria@eduadapt.local` | `aluno123` |
| Aluno Joao | `joao@eduadapt.local` | `aluno123` |

## 5. Ver logs

Todos os servicos:

```powershell
docker compose logs -f
```

Somente backend:

```powershell
docker compose logs -f api
```

Somente frontend:

```powershell
docker compose logs -f web
```

Somente banco:

```powershell
docker compose logs -f postgres
```

## 6. Parar o projeto

Parar sem apagar dados do banco:

```powershell
docker compose down
```

Parar e apagar o volume do banco:

```powershell
docker compose down -v
```

Use `down -v` somente quando quiser resetar completamente os dados locais.

## 7. Rebuild

Se mudar dependencias do backend, por exemplo `apps/api/requirements.txt`:

```powershell
docker compose build api
docker compose up -d api
```

Se mudar dependencias do frontend, por exemplo `apps/web/package.json`:

```powershell
docker compose build web
docker compose up -d web
```

Para rebuild completo:

```powershell
docker compose build --no-cache
docker compose up -d
```

## 8. Problemas comuns

### Docker Desktop fechado

Erro comum:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

Solucao:

1. Abra o Docker Desktop.
2. Aguarde o status ficar como "Running".
3. Rode novamente:

```powershell
docker compose up -d
```

### Porta ocupada

Se `3000`, `8000` ou `5432` ja estiverem em uso, o Docker Compose pode falhar.

Verifique processos usando as portas:

```powershell
netstat -ano | findstr :3000
netstat -ano | findstr :8000
netstat -ano | findstr :5432
```

### API subiu, mas frontend nao conecta

Confirme que o frontend aponta para:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

No `docker-compose.yml`, essa variavel ja esta configurada para o servico `web`.

### Seed ou migrations falhando

Ver logs da API:

```powershell
docker compose logs -f api
```

A API executa automaticamente:

```bash
alembic upgrade head
python -m app.seeds.initial
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## 9. Comando rapido completo

```powershell
cd C:\Repositores\Edu-Adapt-AI
docker compose up -d
docker compose ps
```

Depois abra:

```text
http://localhost:3000
```
