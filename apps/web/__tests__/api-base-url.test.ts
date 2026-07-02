/**
 * Testes para apps/web/lib/api.ts
 *
 * Validam que:
 * 1. NEXT_PUBLIC_API_URL é usada quando definida
 * 2. Em dev, localhost é o fallback (conveniente)
 * 3. Em produção, sem NEXT_PUBLIC_API_URL, NÃO usa localhost (evita silent failure)
 *
 * Nota: process.env.NODE_ENV é substituído literalmente pelo compilador Next.js/SWC
 * em tempo de build (valor "test" em Jest). Por isso a lógica de produção é testada
 * via a função pura _getApiBaseUrl em vez de manipular NODE_ENV em runtime.
 */
export {}; // módulo isolado — evita colisão de variáveis globais com outros test files

jest.mock("js-cookie", () => ({
  get: jest.fn(),
  set: jest.fn(),
  remove: jest.fn(),
}));

import { _getApiBaseUrl } from "@/lib/api";

// ── Testes da função pura (sem deps de process.env) ──────────────────────────

describe("_getApiBaseUrl — lógica pura", () => {
  it("usa apiUrl quando fornecida, em qualquer ambiente", () => {
    expect(_getApiBaseUrl("https://eduadapt-api.is-a.dev", true)).toBe(
      "https://eduadapt-api.is-a.dev"
    );
    expect(_getApiBaseUrl("https://eduadapt-api.is-a.dev", false)).toBe(
      "https://eduadapt-api.is-a.dev"
    );
  });

  it("usa ngrok static domain quando fornecido", () => {
    expect(_getApiBaseUrl("https://eduadapt-api.ngrok-free.app", true)).toBe(
      "https://eduadapt-api.ngrok-free.app"
    );
  });

  it("retorna string vazia em produção sem apiUrl — não cai em localhost", () => {
    expect(_getApiBaseUrl(undefined, true)).toBe("");
    expect(_getApiBaseUrl(undefined, true)).not.toBe("http://localhost:8000");
  });

  it("retorna localhost em desenvolvimento sem apiUrl — fallback esperado", () => {
    expect(_getApiBaseUrl(undefined, false)).toBe("http://localhost:8000");
  });
});

// ── Testes de integração do módulo (axios instance) ──────────────────────────

describe("api.ts — instância axios", () => {
  const savedApiUrl = process.env.NEXT_PUBLIC_API_URL;

  afterEach(() => {
    jest.restoreAllMocks();
    if (savedApiUrl === undefined) {
      delete process.env.NEXT_PUBLIC_API_URL;
    } else {
      process.env.NEXT_PUBLIC_API_URL = savedApiUrl;
    }
  });

  it("usa NEXT_PUBLIC_API_URL quando definida", () => {
    process.env.NEXT_PUBLIC_API_URL = "https://eduadapt-api.is-a.dev";
    jest.spyOn(console, "warn").mockImplementation(() => {});

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let api: any;
    jest.isolateModules(() => {
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      api = require("@/lib/api").default;
    });

    expect(api.defaults.baseURL).toBe("https://eduadapt-api.is-a.dev");
  });

  it("cai em localhost em ambiente não-produção sem NEXT_PUBLIC_API_URL (NODE_ENV=test)", () => {
    delete process.env.NEXT_PUBLIC_API_URL;
    jest.spyOn(console, "warn").mockImplementation(() => {});

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    let api: any;
    jest.isolateModules(() => {
      // eslint-disable-next-line @typescript-eslint/no-require-imports
      api = require("@/lib/api").default;
    });

    // Em Jest (NODE_ENV=test), IS_PRODUCTION é false → fallback localhost
    expect(api.defaults.baseURL).toBe("http://localhost:8000");
  });
});
