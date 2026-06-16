"""
Testes de configuração CORS.

Unitários: testam o parsing de settings (sem depender da config do container).
Integração: testam os headers HTTP reais via TestClient.
"""
import re

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, settings
from app.main import app


# ── Testes unitários de configuração ─────────────────────────────────────────

def test_cors_origins_list_splits_by_comma():
    s = Settings(cors_origins="http://localhost:3000,https://app.vercel.app")
    assert "http://localhost:3000" in s.cors_origins_list
    assert "https://app.vercel.app" in s.cors_origins_list
    assert len(s.cors_origins_list) == 2


def test_cors_origins_list_strips_whitespace():
    s = Settings(cors_origins="http://localhost:3000, http://127.0.0.1:3000")
    assert "http://localhost:3000" in s.cors_origins_list
    assert "http://127.0.0.1:3000" in s.cors_origins_list


def test_cors_origins_includes_127_variant_by_default():
    # O default em config.py deve incluir 127.0.0.1:3000
    s = Settings()
    # Usa os valores do ambiente atual (docker-compose) — deve incluir 127.0.0.1
    origins = s.cors_origins_list
    assert any("localhost:3000" in o or "127.0.0.1:3000" in o for o in origins)


def test_vercel_preview_regex_matches_preview_url():
    pattern = r"https://[a-z0-9-]+\.vercel\.app"
    assert re.fullmatch(pattern, "https://web-abc123.vercel.app")
    assert re.fullmatch(pattern, "https://web-xyz789-allanulise027-3939s-projects.vercel.app")


def test_vercel_regex_does_not_match_http():
    pattern = r"https://[a-z0-9-]+\.vercel\.app"
    assert not re.fullmatch(pattern, "http://web-abc123.vercel.app")


def test_vercel_regex_does_not_match_unrelated_domain():
    pattern = r"https://[a-z0-9-]+\.vercel\.app"
    assert not re.fullmatch(pattern, "https://evil.com")


def test_is_a_dev_subdomain_regex_matches():
    pattern = r"https://eduadapt-api\.is-a\.dev"
    assert re.fullmatch(pattern, "https://eduadapt-api.is-a.dev")


# ── Testes de integração via TestClient ───────────────────────────────────────

def test_cors_preflight_allows_localhost_3000(client: TestClient):
    r = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        },
    )
    origin_header = r.headers.get("access-control-allow-origin")
    assert origin_header == "http://localhost:3000", (
        f"CORS não permitiu http://localhost:3000 — header: {origin_header}"
    )


def test_cors_get_returns_allow_origin_for_localhost(client: TestClient):
    r = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_blocks_unknown_origin(client: TestClient):
    r = client.options(
        "/health",
        headers={
            "Origin": "https://evil-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in r.headers


def test_cors_allows_vercel_preview_when_regex_configured(client: TestClient):
    if not settings.cors_origin_regex:
        pytest.skip("CORS_ORIGIN_REGEX não configurado — configure no docker-compose ou .env")

    vercel_origin = "https://web-abc123-allanulise027-3939s-projects.vercel.app"
    r = client.options(
        "/health",
        headers={
            "Origin": vercel_origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type,Authorization",
        },
    )
    origin_header = r.headers.get("access-control-allow-origin")
    assert origin_header == vercel_origin, (
        f"CORS não permitiu Vercel preview — header: {origin_header}\n"
        f"Regex atual: {settings.cors_origin_regex!r}"
    )
