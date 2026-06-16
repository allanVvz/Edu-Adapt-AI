import axios from "axios";
import Cookies from "js-cookie";

const API_URL = process.env.NEXT_PUBLIC_API_URL;
const IS_PRODUCTION = process.env.NODE_ENV === "production";

// Exportada para testes unitários — isola a lógica sem depender de process.env.
export function _getApiBaseUrl(
  apiUrl: string | undefined,
  isProduction: boolean
): string {
  return apiUrl ?? (isProduction ? "" : "http://localhost:8000");
}

// Em produção, não cair em localhost — não é acessível de nenhum servidor público.
// Em desenvolvimento, localhost é o fallback esperado.
const BASE_URL = _getApiBaseUrl(API_URL, IS_PRODUCTION);

if (typeof window !== "undefined" && !API_URL) {
  if (IS_PRODUCTION) {
    console.error(
      "[EduAdapt] ERRO CRÍTICO: NEXT_PUBLIC_API_URL não está definida.\n" +
        "Configure essa variável nas Environment Variables do projeto na Vercel\n" +
        "apontando para a URL pública do backend (ex: https://eduadapt-api.is-a.dev).\n" +
        "Todas as chamadas de API falharão até que essa variável seja configurada."
    );
  } else {
    console.warn(
      "[EduAdapt] NEXT_PUBLIC_API_URL não definida — usando http://localhost:8000 (dev local)."
    );
  }
}

const api = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = Cookies.get("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      Cookies.remove("token");
      Cookies.remove("user");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
