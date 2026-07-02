"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AdminLayout from "@/components/layout/AdminLayout";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { Plus, UserCircle, X, BookOpen, ExternalLink } from "lucide-react";
import clsx from "clsx";

interface Profile {
  id: string;
  name: string;
  description: string | null;
  reading_level: string | null;
  autonomy_level: string | null;
  main_difficulties: string[] | null;
  recommended_strategies: string[] | null;
  preferred_modalities: string[] | null;
  resources_to_avoid: string[] | null;
  notes: string | null;
  accessibility_complexity: string | null;
}

interface ProfileAdaptation {
  id: string;
  activity_id: string;
  activity_title: string | null;
  status: string;
  version: number;
  generated_by: string;
  created_at: string;
}

const READING: Record<string, string> = {
  initial: "Leitura inicial", basic: "Básico",
  intermediate: "Intermediário", advanced: "Avançado",
};
const AUTONOMY: Record<string, string> = {
  low: "Baixa autonomia", medium: "Média", high: "Alta",
};
const STATUS_LABEL: Record<string, string> = {
  review: "Em revisão", approved: "Aprovado",
  published: "Publicado", rejected: "Reprovado", draft: "Rascunho",
};

const EMPTY_FORM = {
  name: "", description: "", reading_level: "initial", autonomy_level: "low",
  main_difficulties: "", recommended_strategies: "", preferred_modalities: "",
  resources_to_avoid: "", notes: "", accessibility_complexity: "",
};

function toArray(s: string): string[] | null {
  const arr = s.split(",").map((x) => x.trim()).filter(Boolean);
  return arr.length > 0 ? arr : null;
}
function fromArray(a: string[] | null): string {
  return (a || []).join(", ");
}

export default function ProfilesPage() {
  const router = useRouter();
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [editingProfile, setEditingProfile] = useState<Profile | null>(null);
  const [editTab, setEditTab] = useState<"editar" | "atividades">("editar");
  const [adaptations, setAdaptations] = useState<ProfileAdaptation[]>([]);
  const [loadingAdaptations, setLoadingAdaptations] = useState(false);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);

  useEffect(() => { load(); }, []);

  async function load() {
    const { data } = await api.get("/student-profiles").catch(() => ({ data: [] }));
    setProfiles(data);
  }

  function openEdit(p: Profile) {
    setEditingProfile(p);
    setEditTab("editar");
    setForm({
      name: p.name,
      description: p.description || "",
      reading_level: p.reading_level || "initial",
      autonomy_level: p.autonomy_level || "low",
      main_difficulties: fromArray(p.main_difficulties),
      recommended_strategies: fromArray(p.recommended_strategies),
      preferred_modalities: fromArray(p.preferred_modalities),
      resources_to_avoid: fromArray(p.resources_to_avoid),
      notes: p.notes || "",
      accessibility_complexity: p.accessibility_complexity || "",
    });
    setAdaptations([]);
  }

  async function loadAdaptations(profileId: string) {
    setLoadingAdaptations(true);
    try {
      const { data } = await api.get(`/student-profiles/${profileId}/adaptations`);
      setAdaptations(data);
    } catch {
      setAdaptations([]);
    } finally {
      setLoadingAdaptations(false);
    }
  }

  function switchEditTab(tab: "editar" | "atividades") {
    setEditTab(tab);
    if (tab === "atividades" && editingProfile) {
      loadAdaptations(editingProfile.id);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/student-profiles", {
        name: form.name,
        description: form.description || null,
        reading_level: form.reading_level,
        autonomy_level: form.autonomy_level,
        main_difficulties: toArray(form.main_difficulties),
        recommended_strategies: toArray(form.recommended_strategies),
        preferred_modalities: toArray(form.preferred_modalities),
        resources_to_avoid: toArray(form.resources_to_avoid),
        notes: form.notes || null,
        accessibility_complexity: form.accessibility_complexity || null,
      });
      toast.success("Perfil criado.");
      setShowCreate(false);
      setForm({ ...EMPTY_FORM });
      load();
    } catch {
      toast.error("Erro ao criar perfil.");
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveEdit(e: React.FormEvent) {
    e.preventDefault();
    if (!editingProfile) return;
    setSaving(true);
    try {
      await api.put(`/student-profiles/${editingProfile.id}`, {
        name: form.name,
        description: form.description || null,
        reading_level: form.reading_level,
        autonomy_level: form.autonomy_level,
        main_difficulties: toArray(form.main_difficulties),
        recommended_strategies: toArray(form.recommended_strategies),
        preferred_modalities: toArray(form.preferred_modalities),
        resources_to_avoid: toArray(form.resources_to_avoid),
        notes: form.notes || null,
        accessibility_complexity: form.accessibility_complexity || null,
      });
      toast.success("Perfil salvo.");
      setEditingProfile(null);
      load();
    } catch {
      toast.error("Erro ao salvar perfil.");
    } finally {
      setSaving(false);
    }
  }

  const ProfileFormFields = () => (
    <div className="space-y-3">
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Nome do perfil *</label>
        <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Descrição</label>
        <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
          rows={2} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none" />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Nível de leitura</label>
          <select value={form.reading_level} onChange={(e) => setForm({ ...form, reading_level: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
            <option value="initial">Leitura inicial</option>
            <option value="basic">Básico</option>
            <option value="intermediate">Intermediário</option>
            <option value="advanced">Avançado</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-600 mb-1">Autonomia</label>
          <select value={form.autonomy_level} onChange={(e) => setForm({ ...form, autonomy_level: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
            <option value="low">Baixa</option>
            <option value="medium">Média</option>
            <option value="high">Alta</option>
          </select>
        </div>
      </div>
      {[
        { label: "Dificuldades principais (sep. por vírgula)", key: "main_difficulties" },
        { label: "Estratégias recomendadas (sep. por vírgula)", key: "recommended_strategies" },
        { label: "Modalidades preferidas (visual, audio, drag_drop...)", key: "preferred_modalities" },
        { label: "Recursos a evitar (sep. por vírgula)", key: "resources_to_avoid" },
      ].map(({ label, key }) => (
        <div key={key}>
          <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
          <input value={(form as Record<string, string>)[key]}
            onChange={(e) => setForm({ ...form, [key]: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
        </div>
      ))}
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Complexidade de acessibilidade</label>
        <select value={form.accessibility_complexity}
          onChange={(e) => setForm({ ...form, accessibility_complexity: e.target.value })}
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
          <option value="">Não definido</option>
          <option value="minimal">Mínima (pictogramas AAC)</option>
          <option value="low_stimulation">Baixo estímulo (dessaturado)</option>
          <option value="supported">Apoiado (colorido com suporte)</option>
          <option value="standard">Padrão</option>
        </select>
      </div>
      <div>
        <label className="block text-xs font-medium text-gray-600 mb-1">Observações</label>
        <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })}
          rows={2} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none" />
      </div>
    </div>
  );

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Perfis Pedagógicos</h1>
        <button
          onClick={() => { setShowCreate(true); setForm({ ...EMPTY_FORM }); }}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          <Plus size={15} /> Novo perfil
        </button>
      </div>

      {profiles.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
          <UserCircle size={32} className="mx-auto mb-3 opacity-30" />
          <p>Nenhum perfil cadastrado.</p>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2">
          {profiles.map((p) => (
            <button
              key={p.id}
              onClick={() => openEdit(p)}
              className="text-left bg-white rounded-xl border border-gray-200 p-4 hover:border-purple-300 hover:shadow-sm transition-all group"
            >
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-700 flex-shrink-0 group-hover:bg-purple-200 transition-colors">
                  <UserCircle size={16} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-900 text-sm">{p.name}</p>
                  {p.description && <p className="text-xs text-gray-400 mt-0.5 line-clamp-2">{p.description}</p>}
                  <div className="flex flex-wrap gap-1 mt-2">
                    {p.reading_level && (
                      <span className="text-xs bg-blue-50 text-blue-600 rounded-full px-2 py-0.5">{READING[p.reading_level] || p.reading_level}</span>
                    )}
                    {p.autonomy_level && (
                      <span className="text-xs bg-green-50 text-green-600 rounded-full px-2 py-0.5">{AUTONOMY[p.autonomy_level] || p.autonomy_level}</span>
                    )}
                    {p.accessibility_complexity && (
                      <span className="text-xs bg-orange-50 text-orange-600 rounded-full px-2 py-0.5">{p.accessibility_complexity}</span>
                    )}
                  </div>
                  {p.main_difficulties && p.main_difficulties.length > 0 && (
                    <p className="text-xs text-gray-400 mt-1">{p.main_difficulties.slice(0, 2).join(", ")}{p.main_difficulties.length > 2 ? "…" : ""}</p>
                  )}
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">Novo perfil pedagógico</h2>
              <button onClick={() => setShowCreate(false)} className="p-1.5 hover:bg-gray-100 rounded-lg">
                <X size={16} className="text-gray-500" />
              </button>
            </div>
            <form onSubmit={handleCreate} className="space-y-4">
              <ProfileFormFields />
              <div className="flex gap-2 pt-2">
                <button type="submit" disabled={saving}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg">
                  {saving ? "Criando..." : "Criar perfil"}
                </button>
                <button type="button" onClick={() => setShowCreate(false)}
                  className="flex-1 border border-gray-300 text-gray-600 text-sm py-2 rounded-lg">
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit modal */}
      {editingProfile && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] flex flex-col">
            {/* Modal header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <div>
                <h2 className="text-lg font-bold text-gray-900">{editingProfile.name}</h2>
                <p className="text-xs text-gray-400">Clique em "Atividades" para ver as adaptações geradas</p>
              </div>
              <button onClick={() => setEditingProfile(null)} className="p-1.5 hover:bg-gray-100 rounded-lg">
                <X size={16} className="text-gray-500" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 px-6 pt-3 border-b border-gray-100">
              {(["editar", "atividades"] as const).map((t) => (
                <button key={t} onClick={() => switchEditTab(t)}
                  className={clsx("px-4 py-2 text-sm font-medium rounded-t-lg capitalize transition-colors", {
                    "bg-blue-50 text-blue-700 border-b-2 border-blue-600": editTab === t,
                    "text-gray-500 hover:text-gray-700": editTab !== t,
                  })}>
                  {t === "editar" ? "Editar" : "Atividades"}
                </button>
              ))}
            </div>

            {/* Tab body */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
              {editTab === "editar" && (
                <form id="editForm" onSubmit={handleSaveEdit} className="space-y-4">
                  <ProfileFormFields />
                </form>
              )}

              {editTab === "atividades" && (
                <div>
                  {loadingAdaptations ? (
                    <div className="flex justify-center py-10">
                      <div className="animate-spin h-6 w-6 border-4 border-blue-500 border-t-transparent rounded-full" />
                    </div>
                  ) : adaptations.length === 0 ? (
                    <div className="text-center py-12 text-gray-400">
                      <BookOpen size={28} className="mx-auto mb-2 opacity-30" />
                      <p className="text-sm">Nenhuma atividade adaptada para este perfil ainda.</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {adaptations.map((a) => (
                        <div key={a.id} className="flex items-center justify-between bg-gray-50 rounded-xl px-4 py-3 border border-gray-100">
                          <div>
                            <p className="text-sm font-medium text-gray-800">{a.activity_title || "Atividade"}</p>
                            <div className="flex items-center gap-2 mt-0.5">
                              <span className={clsx("text-xs rounded-full px-2 py-0.5", {
                                "bg-yellow-100 text-yellow-700": a.status === "review",
                                "bg-green-100 text-green-700": a.status === "approved" || a.status === "published",
                                "bg-red-100 text-red-700": a.status === "rejected",
                                "bg-gray-100 text-gray-500": a.status === "draft",
                              })}>
                                {STATUS_LABEL[a.status] || a.status}
                              </span>
                              <span className="text-xs text-gray-400">v{a.version}</span>
                              <span className="text-xs text-gray-400">via {a.generated_by}</span>
                            </div>
                          </div>
                          <button
                            onClick={() => router.push(`/adaptations/${a.id}/review`)}
                            className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
                          >
                            <ExternalLink size={12} /> Abrir
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Footer */}
            {editTab === "editar" && (
              <div className="px-6 py-4 border-t border-gray-100 flex gap-2">
                <button type="submit" form="editForm" disabled={saving}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg">
                  {saving ? "Salvando..." : "Salvar"}
                </button>
                <button type="button" onClick={() => setEditingProfile(null)}
                  className="flex-1 border border-gray-300 text-gray-600 text-sm py-2 rounded-lg">
                  Cancelar
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
