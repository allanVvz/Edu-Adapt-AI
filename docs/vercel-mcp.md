# Integração Vercel via MCP Claude

## Visão geral

O EduAdapt AI utiliza uma arquitetura híbrida:
- **Frontend (Next.js):** hospedado no Vercel
- **Backend (FastAPI) + Banco (PostgreSQL):** hospedado em servidor VPS ou container Docker

O MCP (Model Context Protocol) do Claude permite que o assistente execute deploys, consulte logs e gerencie projetos Vercel diretamente na conversa.

---

## 1. Pré-requisitos

1. Conta no Vercel em [vercel.com](https://vercel.com)
2. Projeto Next.js já criado no Vercel (ou via CLI)
3. Claude Code com acesso ao MCP do Vercel
4. Token de acesso do Vercel

---

## 2. Criar token do Vercel

1. Acesse [vercel.com/account/tokens](https://vercel.com/account/tokens)
2. Clique em **Create Token**
3. Dê um nome como `eduadapt-mcp`
4. Selecione escopo **Full Access** ou apenas o projeto específico
5. Copie o token gerado

---

## 3. Variáveis de ambiente necessárias

### No Vercel (frontend)

```env
NEXT_PUBLIC_API_URL=https://api.seu-dominio.com
```

### No backend (Docker / VPS)

```env
CORS_ORIGINS=https://seu-projeto.vercel.app,http://localhost:3000
DATABASE_URL=postgresql://...
SECRET_KEY=...
```

---

## 4. Configurar MCP no Claude Code

### Via settings do Claude Code

```json
{
  "mcpServers": {
    "vercel": {
      "command": "npx",
      "args": ["-y", "@vercel/mcp-server"],
      "env": {
        "VERCEL_TOKEN": "seu-token-aqui"
      }
    }
  }
}
```

Ou adicione o token nas API Keys da tela `/settings/api-keys` e referencie via variável de ambiente.

---

## 5. Usar MCP para deploy

Com o MCP configurado, você pode fazer deploy do frontend diretamente no Claude Code:

```
Deploy o frontend do EduAdapt AI no Vercel
```

O MCP vai:
1. Detectar o projeto Next.js em `apps/web/`
2. Fazer o build
3. Deploy para o projeto configurado
4. Retornar a URL de preview

---

## 6. Separação frontend / backend

```
Browser → vercel.app (Next.js)
               ↓ chamadas API
          api.seu-dominio.com:8000 (FastAPI no VPS)
               ↓
          postgres:5432 (PostgreSQL no mesmo servidor)
```

### Configurar domínio do backend

1. Suba o backend com Docker Compose no VPS
2. Configure Nginx ou Traefik para expor a porta 8000
3. Configure HTTPS com Let's Encrypt
4. Atualize `NEXT_PUBLIC_API_URL` no Vercel para apontar ao domínio do backend

---

## 7. Comandos úteis via MCP

```
# Listar projetos
list_projects

# Ver último deploy
list_deployments

# Ver logs de build
get_deployment_build_logs

# Ver logs de runtime
get_runtime_logs

# Verificar domínio
check_domain_availability_and_price
```

---

## 8. Próximos passos

- [ ] Criar projeto no Vercel manualmente ou via CLI
- [ ] Adicionar `NEXT_PUBLIC_API_URL` nas env vars do Vercel
- [ ] Configurar domínio personalizado
- [ ] Configurar HTTPS no backend (VPS)
- [ ] Testar deploy via MCP Claude
- [ ] Configurar CI/CD automático via GitHub Actions

---

## 9. Referências

- [Vercel MCP Server](https://vercel.com/docs/mcp)
- [Claude Code MCP Docs](https://docs.anthropic.com/claude/docs/mcp)
- [Next.js Deploy](https://nextjs.org/docs/deployment)
