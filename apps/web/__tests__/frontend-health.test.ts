/**
 * @jest-environment node
 *
 * Frontend smoke test — validates that the Next.js dev server is reachable
 * and returns a valid HTML response on port 3000.
 *
 * Runs inside the web Docker container via `docker compose exec -T web npm test`.
 * The Next.js server must already be running (started by the container entrypoint).
 */

const http = require("http");

const BASE_URL = process.env.TEST_FRONTEND_URL ?? "http://localhost:3000";
const TIMEOUT_MS = 10_000;

function httpGet(url: string): Promise<{ status: number; body: string }> {
  return new Promise((resolve, reject) => {
    const req = http.get(url, { timeout: TIMEOUT_MS }, (res: { statusCode: number; setEncoding: (e: string) => void; on: (e: string, cb: (chunk: string) => void) => void }) => {
      let body = "";
      res.setEncoding("utf8");
      res.on("data", (chunk: string) => { body += chunk; });
      res.on("end", () => resolve({ status: res.statusCode, body }));
    });
    req.on("error", reject);
    req.on("timeout", () => { req.destroy(); reject(new Error(`Request to ${url} timed out after ${TIMEOUT_MS}ms`)); });
  });
}

describe("Frontend health", () => {
  it("GET / responds with HTTP 200", async () => {
    const { status } = await httpGet(BASE_URL);
    expect(status).toBe(200);
  });

  it("GET / returns HTML content", async () => {
    const { body } = await httpGet(BASE_URL);
    // Next.js always serves a DOCTYPE — if it's an error page it won't have this
    expect(body.toLowerCase()).toContain("<!doctype html>");
  });

  it("GET /login responds with HTTP 200", async () => {
    const { status } = await httpGet(`${BASE_URL}/login`);
    expect(status).toBe(200);
  });
});
