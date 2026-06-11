"use client";
import { useEffect, useState } from "react";
import AdminLayout from "@/components/layout/AdminLayout";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { Plus, UserCircle } from "lucide-react";

interface Profile {
  id: string;
  name: string;
  description: string | null;
  reading_level: string | null;
  autonomy_level: string | null;
  main_difficulties: string[] | null;
  preferred_modalities: string[] | null;
}

const READING = { initial: "Leitura inicial", basic: "Básico", intermediate: "Intermediário", advanced: "Avançado" } as Record<string, string>;
const AUTONOMY = { low: "Baixa autonomia", medium: "Média", high: "Alta" } as Record<string, string>;

export default function ProfilesPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    name: "", description: "", reading_level: "basic", autonomy_level: "medium",
    main_difficulties: "", recommended_strategies: "", preferred_modalities: "", resources_to_avoid: "", notes: "",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => { load(); }, []);

  async function load() {
    const { data } = await api.get("/student-profiles").catch(() => ({ data: [] }));
    setProfiles(data);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      const payload = {
        name: form.name,
        description: form.description || null,
        reading_level: form.reading_level,
        autonomy_level: form.autonomy_level,
        main_difficulties: form.main_difficulties ? form.main_difficulties.split(",").map((s) => s.trim()) : null,
        recommended_strategies: form.recommended_strategies ? form.recommended_strategies.split(",").map((s) => s.trim()) : null,
        preferred_modalities: form.preferred_modalities ? form.preferred_modalities.split(",").map((s) => s.trim()) : null,
        resources_to_avoid: form.resources_to_avoid ? form.resources_to_avoid.split(",").map((s) => s.trim()) : null,
        notes: form.notes || null,
      };
      await api.post("/student-profiles", payload);
      toast.success("Perfil criado.");
      setShowModal(false);
      load();
    } catch {
      toast.error("Erro ao criar perfil.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Perfis Pedagógicos</h1>
        <button
          onClick={() => setShowModal(true)}
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
            <div key={p.id} className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-700 flex-shrink-0">
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
                  </div>
                  {p.main_difficulties && p.main_difficulties.length > 0 && (
                    <p className="text-xs text-gray-400 mt-1">{p.main_difficulties.slice(0, 2).join(", ")}{p.main_difficulties.length > 2 ? "…" : ""}</p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Novo perfil pedagógico</h2>
            <form onSubmit={handleCreate} className="space-y-3">
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
                { label: "Dificuldades principais (separadas por vírgula)", key: "main_difficulties" },
                { label: "Estratégias recomendadas (separadas por vírgula)", key: "recommended_strategies" },
                { label: "Modalidades preferidas (visual, audio, drag_drop...)", key: "preferred_modalities" },
                { label: "Recursos a evitar (separados por vírgula)", key: "resources_to_avoid" },
              ].map(({ label, key }) => (
                <div key={key}>
                  <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
                  <input value={(form as Record<string, string>)[key]}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
                </div>
              ))}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Observações</label>
                <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  rows={2} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none" />
              </div>
              <div className="flex gap-2 pt-2">
                <button type="submit" disabled={saving}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg">
                  {saving ? "Criando..." : "Criar perfil"}
                </button>
                <button type="button" onClick={() => setShowModal(false)}
                  className="flex-1 border border-gray-300 text-gray-600 text-sm py-2 rounded-lg">
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
