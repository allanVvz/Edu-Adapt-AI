import Cookies from "js-cookie";

export interface AuthUser {
  id: string;
  name: string;
  email: string;
  role: "admin" | "teacher" | "student";
}

export function getUser(): AuthUser | null {
  try {
    const raw = Cookies.get("user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function setAuth(token: string, user: AuthUser) {
  Cookies.set("token", token, { expires: 1 });
  Cookies.set("user", JSON.stringify(user), { expires: 1 });
}

export function clearAuth() {
  Cookies.remove("token");
  Cookies.remove("user");
}

export function isTeacherOrAdmin(user: AuthUser | null): boolean {
  return user?.role === "admin" || user?.role === "teacher";
}
