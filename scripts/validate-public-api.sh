#!/usr/bin/env bash
# Valida que o backend EduAdapt AI está acessível publicamente.
# Uso:
#   ./scripts/validate-public-api.sh https://eduadapt-api.is-a.dev
#   NEXT_PUBLIC_API_URL=https://... ./scripts/validate-public-api.sh
set -euo pipefail

API_URL="${1:-${NEXT_PUBLIC_API_URL:-}}"

if [ -z "$API_URL" ]; then
  echo "Erro: URL da API necessária."
  echo ""
  echo "Uso: $0 <URL>"
  echo "  Ex: $0 https://eduadapt-api.is-a.dev"
  echo "  ou: NEXT_PUBLIC_API_URL=https://... $0"
  exit 1
fi

API_URL="${API_URL%/}"   # remove barra final
VERCEL_PREVIEW="https://web-abc123-allanulise027-3939s-projects.vercel.app"
FAIL=0

echo ""
echo "═══════════════════════════════════════════════════"
echo "  EduAdapt AI — Validação de API Pública"
echo "  URL: $API_URL"
echo "═══════════════════════════════════════════════════"
echo ""

# ── 1. Health check ──────────────────────────────────────────────────────────
echo "1. GET /health"
HTTP_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$API_URL/health" 2>/dev/null || echo "000")
if [ "$HTTP_CODE" = "200" ]; then
  echo "   ✓ HTTP 200 OK"
else
  echo "   ✗ HTTP $HTTP_CODE (esperado 200)"
  [ "$HTTP_CODE" = "000" ] && echo "     → backend inacessível ou URL incorreta"
  FAIL=1
fi

# ── 2. Swagger /docs ─────────────────────────────────────────────────────────
echo ""
echo "2. GET /docs"
DOCS_CODE=$(curl -sf -o /dev/null -w "%{http_code}" "$API_URL/docs" 2>/dev/null || echo "000")
if [ "$DOCS_CODE" = "200" ]; then
  echo "   ✓ HTTP 200 OK"
else
  echo "   ✗ HTTP $DOCS_CODE"
  FAIL=1
fi

# ── 3. CORS preflight — Vercel preview ───────────────────────────────────────
echo ""
echo "3. CORS preflight — Origin: Vercel preview"
CORS_RESP=$(curl -si -X OPTIONS \
  -H "Origin: $VERCEL_PREVIEW" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type,Authorization" \
  "$API_URL/health" 2>/dev/null || true)

if echo "$CORS_RESP" | grep -qi "access-control-allow-origin"; then
  ORIGIN_VAL=$(echo "$CORS_RESP" | grep -i "access-control-allow-origin" | head -1 | tr -d '\r\n')
  echo "   ✓ $ORIGIN_VAL"
else
  echo "   ✗ Header access-control-allow-origin ausente"
  echo "     → Verifique CORS_ORIGIN_REGEX no backend"
  FAIL=1
fi

# ── 4. CORS preflight — localhost ─────────────────────────────────────────────
echo ""
echo "4. CORS preflight — Origin: http://localhost:3000"
CORS_LOCAL=$(curl -si -X OPTIONS \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  "$API_URL/health" 2>/dev/null || true)

if echo "$CORS_LOCAL" | grep -qi "access-control-allow-origin"; then
  echo "   ✓ CORS permitido para localhost"
else
  echo "   ✗ CORS bloqueado para localhost"
  echo "     → Verifique CORS_ORIGINS no backend"
  FAIL=1
fi

# ── Resultado ─────────────────────────────────────────────────────────────────
echo ""
echo "═══════════════════════════════════════════════════"
if [ $FAIL -eq 0 ]; then
  echo "  ✓ Todos os checks passaram"
  echo "  Configure na Vercel: NEXT_PUBLIC_API_URL=$API_URL"
else
  echo "  ✗ Um ou mais checks falharam — veja acima"
fi
echo "═══════════════════════════════════════════════════"
echo ""

exit $FAIL
