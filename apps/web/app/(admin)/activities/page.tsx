"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AdminLayout from "@/components/layout/AdminLayout";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { Plus, BookOpen, Sparkles } from "lucide-react";

interface Activity {
  id: string;
  title: string;
  discipline: string | null;
  school_year: string | null;
  activity_type: string | null;
  base_complexity: number;
  status: string;
}

interface Profile {
  id: string;
  name: string;
}

const TYPE_LABEL: Record<string, string> = {
  multiple_choice: "Múltipla escolha",
  essay: "Dissertativa",
  association: "Associação",
  drag_drop: "Arrastar e soltar",
  game: "Brincadeira",
};

export default function ActivitiesPage() {
  const router = useRouter();
  const [activities, setActivities] = useState<Activity[]>([]);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [adaptingId, setAdaptingId] = useState<string | null>(null);
  const [selectedProfile, setSelectedProfile] = useState("");
  const [form, setForm] = useState({
    title: "", discipline: "", school_year: "", pedagogical_objective: "",
    activity_type: "association", statement: "", question: "", expected_answer: "",
    base_complexity: 2, original_modality: "association",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => { load(); }, []);

  async function load() {
    const [a, p] = await Promise.all([
      api.get("/activities").catch(() => ({ data: [] })),
      api.get("/student-profiles").catch(() => ({ data: [] })),
    ]);
    setActivities(a.data);
    setProfiles(p.data);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/activities", form);
      toast.success("Atividade criada.");
      setShowModal(false);
      load();
    } catch {
      toast.error("Erro ao criar atividade.");
    } finally {
      setSaving(false);
    }
  }

  async function handleAdapt(activityId: string) {
    try {
      toast.loading("Gerando adaptação...", { id: "adapt" });
      const { data } = await api.post(`/activities/${activityId}/adapt`, {
        profile_id: selectedProfile || null,
      });
      toast.dismiss("adapt");
      if (data.no_openai_key) {
        toast("Adaptação gerada com mock. Cadastre uma chave OpenAI para usar IA.", { icon: "⚠️" });
      } else {
        toast.success("Adaptação gerada com IA!");
      }
      router.push(`/adaptations/${data.id}/review`);
    } catch {
      toast.dismiss("adapt");
      toast.error("Erro ao gerar adaptação.");
    }
  }

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Atividades</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          <Plus size={15} /> Nova atividade
        </button>
      </div>

      {activities.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
          <BookOpen size={32} className="mx-auto mb-3 opacity-30" />
          <p>Nenhuma atividade cadastrada.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {activities.map((a) => (
            <div key={a.id} className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-900">{a.title}</p>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {a.discipline && <span className="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-0.5">{a.discipline}</span>}
                    {a.school_year && <span className="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-0.5">{a.school_year}</span>}
                    {a.activity_type && <span className="text-xs bg-blue-50 text-blue-600 rounded-full px-2 py-0.5">{TYPE_LABEL[a.activity_type] || a.activity_type}</span>}
                    <span className={`text-xs rounded-full px-2 py-0.5 ${a.status === "active" ? "bg-green-50 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                      {a.status === "active" ? "Ativa" : a.status}
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <select
                    value={adaptingId === a.id ? selectedProfile : ""}
                    onChange={(e) => { setAdaptingId(a.id); setSelectedProfile(e.target.value); }}
                    className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 max-w-[140px]"
                  >
                    <option value="">Sem perfil</option>
                    {profiles.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                  </select>
                  <button
                    onClick={() => handleAdapt(a.id)}
                    className="flex items-center gap-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg whitespace-nowrap"
                  >
                    <Sparkles size={12} /> Adaptar
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Nova atividade</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Título *</label>
                <input required value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Disciplina</label>
                  <input value={form.discipline} onChange={(e) => setForm({ ...form, discipline: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Ano escolar</label>
                  <input value={form.school_year} onChange={(e) => setForm({ ...form, school_year: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Tipo</label>
                <select value={form.activity_type} onChange={(e) => setForm({ ...form, activity_type: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm">
                  <option value="association">Associação</option>
                  <option value="multiple_choice">Múltipla escolha</option>
                  <option value="essay">Dissertativa</option>
                  <option value="drag_drop">Arrastar e soltar</option>
                  <option value="game">Brincadeira</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Enunciado</label>
                <textarea value={form.statement} onChange={(e) => setForm({ ...form, statement: e.target.value })}
                  rows={2} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Pergunta</label>
                <input value={form.question} onChange={(e) => setForm({ ...form, question: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Resposta esperada</label>
                <textarea value={form.expected_answer} onChange={(e) => setForm({ ...form, expected_answer: e.target.value })}
                  rows={2} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none" />
              </div>
              <div className="flex gap-2 pt-2">
                <button type="submit" disabled={saving}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg">
                  {saving ? "Criando..." : "Criar"}
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
