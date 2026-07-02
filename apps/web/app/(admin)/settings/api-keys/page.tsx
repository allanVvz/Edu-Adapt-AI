"use client";
import { useEffect, useState } from "react";
import AdminLayout from "@/components/layout/AdminLayout";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { Trash2, Plus, Key, Loader2, ImageIcon, CheckCircle, XCircle } from "lucide-react";

const PROVIDERS = [
  { id: "openai", label: "OpenAI API Key", required: true, hint: "Necessária para gerar adaptações com IA." },
  { id: "anthropic", label: "Claude (Anthropic) API Key", required: false, hint: "Opcional." },
  { id: "vercel", label: "Vercel Token", required: false, hint: "Para deploy via MCP." },
  { id: "mcp", label: "MCP Server URL", required: false, hint: "URL do servidor MCP configurado." },
  { id: "ai_brain", label: "AI Brain API Key", required: false, hint: "Integração com AI Brain externo." },
];

interface ApiKeyRecord {
  id: string;
  provider: string;
  key_name: string;
  status: string;
}

export default function ApiKeysPage() {
  const [keys, setKeys] = useState<ApiKeyRecord[]>([]);
  const [form, setForm] = useState({ provider: "openai", key_name: "Minha chave OpenAI", value: "" });
  const [adding, setAdding] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, { ok: boolean; hint?: string; url?: string }>>({});

  useEffect(() => { load(); }, []);

  async function load() {
    try {
      const { data } = await api.get("/settings/api-keys");
      setKeys(data);
    } catch { }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    if (!form.value.trim()) { toast.error("Informe a chave."); return; }
    setAdding(true);
    try {
      await api.post("/settings/api-keys", form);
      toast.success("Chave salva com sucesso.");
      setForm({ provider: "openai", key_name: "Minha chave OpenAI", value: "" });
      setShowForm(false);
      load();
    } catch {
      toast.error("Erro ao salvar chave.");
    } finally {
      setAdding(false);
    }
  }

  async function handleDelete(id: string) {
    await api.delete(`/settings/api-keys/${id}`);
    toast.success("Chave removida.");
    load();
  }

  async function testImageGeneration(id: string) {
    setTestingId(id);
    setTestResults((r) => ({ ...r, [id]: { ok: false } }));
    try {
      const { data } = await api.post(`/settings/api-keys/${id}/test-images`);
      setTestResults((r) => ({ ...r, [id]: data }));
      if (data.ok) {
        toast.success(`Imagem gerada com sucesso! Modelo: ${data.model}`);
      } else {
        toast.error(data.hint || data.error || "Falha na geração de imagem", { duration: 10000 });
      }
    } catch {
      toast.error("Erro ao testar chave.");
    } finally {
      setTestingId(null);
    }
  }

  const hasOpenAI = keys.some((k) => k.provider === "openai" && k.status === "active");

  return (
    <AdminLayout>
      <div className="max-w-2xl">
        <h1 className="text-xl font-bold text-gray-900 mb-2">Chaves de API</h1>

        {!hasOpenAI && (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 rounded-xl p-4 mb-6 text-sm">
            <strong>Atenção:</strong> Para gerar adaptações com texto, áudio e imagens ilustrativas, cadastre sua chave da OpenAI.
          </div>
        )}

        <div className="bg-white rounded-xl border border-gray-200 mb-6">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-700 flex items-center gap-2"><Key size={15} /> Chaves cadastradas</h2>
            <button
              onClick={() => setShowForm(!showForm)}
              className="flex items-center gap-1.5 text-sm text-blue-600 hover:text-blue-800 font-medium"
            >
              <Plus size={15} /> Nova chave
            </button>
          </div>

          {showForm && (
            <form onSubmit={handleSave} className="p-5 bg-blue-50 border-b border-blue-100 space-y-3">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Provider</label>
                  <select
                    value={form.provider}
                    onChange={(e) => setForm({ ...form, provider: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
                  >
                    {PROVIDERS.map((p) => (
                      <option key={p.id} value={p.id}>{p.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Nome</label>
                  <input
                    value={form.key_name}
                    onChange={(e) => setForm({ ...form, key_name: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Valor da chave</label>
                <input
                  type="password"
                  value={form.value}
                  onChange={(e) => setForm({ ...form, value: e.target.value })}
                  placeholder="sk-..."
                  className="w-full border border-gray-300 rounded-lg px-2 py-1.5 text-sm"
                />
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={adding}
                  className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-1.5 rounded-lg"
                >
                  {adding ? "Salvando..." : "Salvar"}
                </button>
                <button type="button" onClick={() => setShowForm(false)} className="text-sm text-gray-500 px-4 py-1.5">
                  Cancelar
                </button>
              </div>
            </form>
          )}

          {keys.length === 0 ? (
            <p className="text-sm text-gray-400 p-5">Nenhuma chave cadastrada.</p>
          ) : (
            <div className="divide-y divide-gray-50">
              {keys.map((k) => {
                const result = testResults[k.id];
                return (
                  <div key={k.id} className="px-5 py-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-800">{k.key_name}</p>
                        <p className="text-xs text-gray-400">{PROVIDERS.find((p) => p.id === k.provider)?.label || k.provider}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        {k.provider === "openai" && k.status === "active" && (
                          <button
                            onClick={() => testImageGeneration(k.id)}
                            disabled={testingId === k.id}
                            className="flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800 border border-purple-200 hover:border-purple-400 rounded-lg px-2 py-1 disabled:opacity-50 transition-colors"
                          >
                            {testingId === k.id
                              ? <Loader2 size={11} className="animate-spin" />
                              : result?.ok === true
                                ? <CheckCircle size={11} />
                                : result?.ok === false && testingId !== k.id
                                  ? <XCircle size={11} className="text-red-500" />
                                  : <ImageIcon size={11} />
                            }
                            Testar imagem
                          </button>
                        )}
                        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${k.status === "active" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                          {k.status === "active" ? "Ativa" : "Inativa"}
                        </span>
                        <button onClick={() => handleDelete(k.id)} className="text-gray-300 hover:text-red-500 transition-colors">
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                    {result && !result.ok && result.hint && (
                      <div className="mt-2 text-xs bg-amber-50 border border-amber-200 text-amber-800 rounded-lg p-3">
                        <strong>Problema detectado:</strong> {result.hint}
                      </div>
                    )}
                    {result?.ok && result.url && (
                      <div className="mt-2 flex items-center gap-2 text-xs text-green-700">
                        <CheckCircle size={12} />
                        Imagem gerada com sucesso — chave tem acesso ao modelo de imagem.
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="bg-gray-50 rounded-xl border border-gray-200 p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Providers disponíveis</h3>
          <div className="space-y-2">
            {PROVIDERS.map((p) => (
              <div key={p.id} className="flex items-start gap-2 text-sm">
                <span className={`mt-0.5 w-1.5 h-1.5 rounded-full flex-shrink-0 ${p.required ? "bg-blue-500" : "bg-gray-300"}`} />
                <div>
                  <span className="font-medium text-gray-700">{p.label}</span>
                  {p.required && <span className="ml-1 text-xs text-blue-600">(recomendada)</span>}
                  <p className="text-gray-400 text-xs">{p.hint}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </AdminLayout>
  );
}
