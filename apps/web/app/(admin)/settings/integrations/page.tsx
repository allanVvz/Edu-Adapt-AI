"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AdminLayout from "@/components/layout/AdminLayout";
import { getUser } from "@/lib/auth";
import { ExternalLink, RefreshCw, Rocket, Loader2, Image as ImageIcon } from "lucide-react";
import toast from "react-hot-toast";

interface VercelConfig {
  token: string;
  projectId: string;
  teamId: string;
  deployHookUrl: string;
}

interface CanvaConfig {
  apiKey: string;
}

interface VercelStatus {
  name: string;
  productionUrl: string | null;
  latestDeployment: { id: string; state: string; createdAt: number; url: string } | null;
}

const STORAGE_VERCEL = "eduadapt_vercel_config";
const STORAGE_CANVA = "eduadapt_canva_config";

const STATE_COLORS: Record<string, string> = {
  READY: "bg-green-100 text-green-700",
  ERROR: "bg-red-100 text-red-700",
  BUILDING: "bg-yellow-100 text-yellow-700",
  QUEUED: "bg-gray-100 text-gray-600",
  CANCELED: "bg-gray-100 text-gray-400",
};

export default function IntegrationsPage() {
  const router = useRouter();
  const [vercel, setVercel] = useState<VercelConfig>({ token: "", projectId: "", teamId: "", deployHookUrl: "" });
  const [canva, setCanva] = useState<CanvaConfig>({ apiKey: "" });
  const [vercelStatus, setVercelStatus] = useState<VercelStatus | null>(null);
  const [vercelSaved, setVercelSaved] = useState(false);
  const [canvaSaved, setCanvaSaved] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [deploying, setDeploying] = useState(false);

  useEffect(() => {
    const user = getUser();
    if (!user || user.role !== "admin") {
      router.replace("/dashboard");
      return;
    }
    const savedVercel = localStorage.getItem(STORAGE_VERCEL);
    if (savedVercel) {
      setVercel(JSON.parse(savedVercel));
      setVercelSaved(true);
    }
    const savedCanva = localStorage.getItem(STORAGE_CANVA);
    if (savedCanva) {
      setCanva(JSON.parse(savedCanva));
      setCanvaSaved(true);
    }
  }, []);

  async function fetchVercelStatus() {
    if (!vercel.token || !vercel.projectId) {
      toast.error("Preencha Token e Project ID.");
      return;
    }
    setLoadingStatus(true);
    try {
      const params = new URLSearchParams({ token: vercel.token, projectId: vercel.projectId });
      if (vercel.teamId) params.set("teamId", vercel.teamId);
      const res = await fetch(`/api/integrations/vercel?${params}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      setVercelStatus(data);
      toast.success("Status atualizado.");
    } catch (e: unknown) {
      toast.error((e as Error).message || "Erro ao buscar status.");
    } finally {
      setLoadingStatus(false);
    }
  }

  async function triggerDeploy() {
    if (!vercel.token) { toast.error("Token Vercel é obrigatório."); return; }
    setDeploying(true);
    try {
      const res = await fetch("/api/integrations/vercel", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: vercel.token,
          projectId: vercel.projectId || undefined,
          teamId: vercel.teamId || undefined,
          deployHookUrl: vercel.deployHookUrl || undefined,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error);
      toast.success("Deploy iniciado! Aguarde alguns minutos.");
      setTimeout(fetchVercelStatus, 5000);
    } catch (e: unknown) {
      toast.error((e as Error).message || "Falha ao iniciar deploy.");
    } finally {
      setDeploying(false);
    }
  }

  function saveVercel() {
    localStorage.setItem(STORAGE_VERCEL, JSON.stringify(vercel));
    setVercelSaved(true);
    toast.success("Configuração Vercel salva.");
    fetchVercelStatus();
  }

  function saveCanva() {
    localStorage.setItem(STORAGE_CANVA, JSON.stringify(canva));
    setCanvaSaved(true);
    toast.success("Configuração Canva salva.");
  }

  return (
    <AdminLayout>
      <h1 className="text-xl font-bold text-gray-900 mb-6">Integrações</h1>

      {/* Vercel MCP */}
      <div className="max-w-2xl bg-white rounded-xl border border-gray-200 p-6 mb-6">
        <div className="flex items-start justify-between mb-1">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-black flex items-center justify-center">
              <svg viewBox="0 0 76 65" fill="white" className="w-4 h-4"><path d="M37.5274 0L75.0548 65H0L37.5274 0Z" /></svg>
            </div>
            <h2 className="font-semibold text-gray-800">Vercel MCP</h2>
          </div>
          <span className={`text-xs rounded-full px-2 py-0.5 font-medium ${vercelSaved ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
            {vercelSaved ? "Configurado" : "Não configurado"}
          </span>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          Conecte ao Vercel via MCP para fazer deploy do frontend e acompanhar o link de produção.
        </p>

        <div className="space-y-3 mb-4">
          {([
            { key: "token", label: "Vercel Token", placeholder: "vercel_token_xxx", type: "password" },
            { key: "projectId", label: "Project ID", placeholder: "prj_..." },
            { key: "teamId", label: "Team ID (opcional)", placeholder: "team_..." },
            { key: "deployHookUrl", label: "Deploy Hook URL (opcional)", placeholder: "https://api.vercel.com/v1/integrations/deploy/..." },
          ] as Array<{ key: keyof VercelConfig; label: string; placeholder: string; type?: string }>).map(({ key, label, placeholder, type }) => (
            <div key={key}>
              <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
              <input
                type={type ?? "text"}
                value={vercel[key]}
                onChange={(e) => setVercel((v) => ({ ...v, [key]: e.target.value }))}
                placeholder={placeholder}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          ))}
        </div>

        <div className="flex gap-2 flex-wrap mb-5">
          <button onClick={saveVercel}
            className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
            Salvar configuração
          </button>
          <button onClick={fetchVercelStatus} disabled={loadingStatus}
            className="flex items-center gap-1.5 border border-gray-200 text-gray-600 hover:bg-gray-50 text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50">
            {loadingStatus ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            Verificar status
          </button>
          <button onClick={triggerDeploy} disabled={deploying}
            className="flex items-center gap-1.5 bg-black hover:bg-gray-800 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors disabled:opacity-50">
            {deploying ? <Loader2 size={14} className="animate-spin" /> : <Rocket size={14} />}
            Fazer deploy
          </button>
        </div>

        {vercelStatus && (
          <div className="border border-gray-100 rounded-lg p-4 bg-gray-50 space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium text-gray-600">Projeto</span>
              <span className="text-xs text-gray-800 font-mono">{vercelStatus.name}</span>
            </div>
            {vercelStatus.productionUrl && (
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-600">URL de produção</span>
                <a href={vercelStatus.productionUrl} target="_blank" rel="noopener noreferrer"
                  className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                  {vercelStatus.productionUrl} <ExternalLink size={11} />
                </a>
              </div>
            )}
            {vercelStatus.latestDeployment && (
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-600">Último deploy</span>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${STATE_COLORS[vercelStatus.latestDeployment.state] ?? "bg-gray-100 text-gray-500"}`}>
                    {vercelStatus.latestDeployment.state}
                  </span>
                  <a href={vercelStatus.latestDeployment.url} target="_blank" rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                    Abrir <ExternalLink size={11} />
                  </a>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Canva MCP */}
      <div className="max-w-2xl bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-1">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-lg bg-[#00C4CC] flex items-center justify-center">
              <ImageIcon size={14} color="white" />
            </div>
            <h2 className="font-semibold text-gray-800">Canva MCP</h2>
          </div>
          <span className={`text-xs rounded-full px-2 py-0.5 font-medium ${canvaSaved ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
            {canvaSaved ? "Configurado" : "Não configurado"}
          </span>
        </div>
        <p className="text-sm text-gray-500 mb-4">
          Integre com o Canva para criar e exportar recursos visuais para as adaptações pedagógicas.
          Gere um token em{" "}
          <a href="https://www.canva.com/developers" target="_blank" rel="noopener noreferrer"
            className="text-blue-600 hover:underline inline-flex items-center gap-0.5">
            canva.com/developers <ExternalLink size={11} />
          </a>.
        </p>

        <div className="space-y-3 mb-4">
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Canva API Key</label>
            <input
              type="password"
              value={canva.apiKey}
              onChange={(e) => setCanva({ apiKey: e.target.value })}
              placeholder="OAuthClientID ou API Key"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <button onClick={saveCanva}
          className="bg-[#00C4CC] hover:bg-[#00a8ae] text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">
          Salvar configuração
        </button>
      </div>
    </AdminLayout>
  );
}
