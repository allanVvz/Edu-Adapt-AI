/**
 * Tests for lib/auth.ts — pure cookie-based auth utilities.
 */
import { getUser, setAuth, clearAuth, isTeacherOrAdmin } from "@/lib/auth";

// Simulate Cookies store
const store: Record<string, string> = {};

jest.mock("js-cookie", () => ({
  get: (key: string) => store[key] ?? undefined,
  set: (key: string, value: string) => { store[key] = value; },
  remove: (key: string) => { delete store[key]; },
}));

beforeEach(() => {
  Object.keys(store).forEach((k) => delete store[k]);
});

describe("getUser", () => {
  it("returns null when no cookie is set", () => {
    expect(getUser()).toBeNull();
  });

  it("returns null for malformed cookie", () => {
    store["user"] = "not-valid-json{{{";
    expect(getUser()).toBeNull();
  });
});

describe("setAuth + getUser round-trip", () => {
  it("stores and retrieves admin user", () => {
    setAuth("tok_abc", { id: "1", name: "Admin", email: "admin@test.com", role: "admin" });
    const user = getUser();
    expect(user).not.toBeNull();
    expect(user?.email).toBe("admin@test.com");
    expect(user?.role).toBe("admin");
  });

  it("stores and retrieves student user", () => {
    setAuth("tok_xyz", { id: "2", name: "Aluno", email: "aluno@test.com", role: "student" });
    const user = getUser();
    expect(user?.role).toBe("student");
  });
});

describe("clearAuth", () => {
  it("removes user after clearAuth", () => {
    setAuth("tok_abc", { id: "1", name: "Admin", email: "admin@test.com", role: "admin" });
    clearAuth();
    expect(getUser()).toBeNull();
  });
});

describe("isTeacherOrAdmin", () => {
  it("returns true for admin", () => {
    expect(isTeacherOrAdmin({ id: "1", name: "A", email: "a@a.com", role: "admin" })).toBe(true);
  });

  it("returns true for teacher", () => {
    expect(isTeacherOrAdmin({ id: "2", name: "T", email: "t@t.com", role: "teacher" })).toBe(true);
  });

  it("returns false for student", () => {
    expect(isTeacherOrAdmin({ id: "3", name: "S", email: "s@s.com", role: "student" })).toBe(false);
  });

  it("returns false for null", () => {
    expect(isTeacherOrAdmin(null)).toBe(false);
  });
});
