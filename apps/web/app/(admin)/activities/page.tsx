"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AdminLayout from "@/components/layout/AdminLayout";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { Plus, BookOpen, Sparkles, Search, ChevronDown, User } from "lucide-react";
import clsx from "clsx";

interface Activity {
  id: string;
  title: string;
  discipline: string | null;
  school_year: string | null;
  activity_type: string | null;
  base_complexity: number;
  status: string;
  teacher_name: string | null;
  adaptation_total: number;
  adaptation_pending: number;
  adaptation_published: number;
}

interface Profile { id: string; name: string }
interface Student { id: string; name: string; email: string }

const TYPE_LABEL: Record<string, string> = {
  multiple_choice: "Múltipla escolha",
  essay: "Dissertativa",
  association: "Associação",
  drag_drop: "Arrastar e soltar",
  game: "Brincadeira",
};

const STATUS_FILTERS = [
  { value: "", label: "Todas" },
  { value: "active", label: "Ativas" },
  { value: "draft", label: "Rascunho" },
  { value: "archived", label: "Arquivadas" },
];

const EMPTY_FORM = {
  title: "", discipline: "", school_year: "",
  pedagogical_objective: "", teacher_notes: "",
  activity_type: "association", statement: "", question: "", expected_answer: "",
  base_complexity: 2, original_modality: "association",
};

export default function ActivitiesPage() {
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [students, setStudents] = useState<Student[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  // Per-card adapt selectors
  const [adaptingId, setAdaptingId] = useState<string | null>(null);
  const [selectedProfile, setSelectedProfile] = useState("");
  const [selectedStudent, setSelectedStudent] = useState("");
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const user = getUser();
    setIsAdmin(user?.role === "admin");
    load();
    api.get("/students").then((r) => setStudents(r.data)).catch(() => {});
  }, []);

  async function load(status?: string) {
    const params = status ? `?status=${status}` : "";
    const [a, p] = await Promise.all([
      api.get(`/activities${params}`).catch(() => ({ data: [] })),
      api.get("/student-profiles").catch(() => ({ data: [] })),
    ]);
    setActivities(a.data);
    setProfiles(p.data);
  }

  function handleFilterChange(status: string) {
    setStatusFilter(status);
    load(status);
  }

  const filtered = activities.filter((a) =>
    a.title.toLowerCase().includes(search.toLowerCase()) ||
    (a.discipline ?? "").toLowerCase().includes(search.toLowerCase())
  );

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/activities", form);
      toast.success("Atividade criada.");
      setShowModal(false);
      setForm({ ...EMPTY_FORM });
      load(statusFilter);
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
        student_id: selectedStudent || null,
      });
      toast.dismiss("adapt");
      if (data.no_openai_key) {
        toast("Adaptação gerada. Cadastre uma chave OpenAI para usar IA.", { icon: "⚠️" });
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
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-gray-900">Atividades</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          <Plus size={15} /> Nova atividade
        </button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-5 flex-wrap">
        <div className="flex gap-1 bg-gray-100 p-1 rounded-lg">
          {STATUS_FILTERS.map(({ value, label }) => (
            <button key={value} onClick={() => handleFilterChange(value)}
              className={clsx("px-3 py-1.5 text-xs font-medium rounded-md transition-colors",
                statusFilter === value ? "bg-white text-blue-700 shadow-sm" : "text-gray-500 hover:text-gray-700"
              )}>
              {label}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input value={search} onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por título ou disciplina..."
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        </div>
        <span className="text-xs text-gray-400">{filtered.length} resultado{filtered.length !== 1 ? "s" : ""}</span>
      </div>

      {filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
          <BookOpen size={32} className="mx-auto mb-3 opacity-30" />
          <p>Nenhuma atividade encontrada.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {filtered.map((a) => (
            <div key={a.id} className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-semibold text-gray-900">{a.title}</p>
                    {isAdmin && a.teacher_name && (
                      <span className="text-xs text-gray-400 bg-gray-50 border border-gray-100 rounded-full px-2 py-0.5">
                        {a.teacher_name}
                      </span>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-1.5 mt-1.5">
                    {a.discipline && <span className="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-0.5">{a.discipline}</span>}
                    {a.school_year && <span className="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-0.5">{a.school_year}</span>}
                    {a.activity_type && <span className="text-xs bg-blue-50 text-blue-600 rounded-full px-2 py-0.5">{TYPE_LABEL[a.activity_type] || a.activity_type}</span>}
                    <span className={clsx("text-xs rounded-full px-2 py-0.5", {
                      "bg-green-50 text-green-700": a.status === "active",
                      "bg-gray-100 text-gray-500": a.status === "draft",
                      "bg-red-50 text-red-500": a.status === "archived",
                    })}>
                      {a.status === "active" ? "Ativa" : a.status === "draft" ? "Rascunho" : "Arquivada"}
                    </span>
                  </div>
                  <div className="flex gap-3 mt-2">
                    {a.adaptation_total > 0 && (
                      <>
                        <span className="text-xs text-gray-400">{a.adaptation_total} adaptação{a.adaptation_total !== 1 ? "ões" : ""}</span>
                        {a.adaptation_pending > 0 && (
                          <span className="text-xs text-yellow-600 font-medium">{a.adaptation_pending} pendente{a.adaptation_pending !== 1 ? "s" : ""}</span>
                        )}
                        {a.adaptation_published > 0 && (
                          <span className="text-xs text-green-600 font-medium">{a.adaptation_published} publicada{a.adaptation_published !== 1 ? "s" : ""}</span>
                        )}
                      </>
                    )}
                  </div>
                </div>

                {/* Adapt section */}
                <div className="flex flex-col gap-1.5 items-end">
                  <div className="flex items-center gap-1.5">
                    {/* Profile select */}
                    <div className="relative">
                      <select
                        value={adaptingId === a.id ? selectedProfile : ""}
                        onChange={(e) => { setAdaptingId(a.id); setSelectedProfile(e.target.value); }}
                        className="text-xs border border-gray-200 rounded-lg pl-2 pr-6 py-1.5 max-w-[130px] appearance-none"
                        title="Perfil pedagógico"
                      >
                        <option value="">Sem perfil</option>
                        {profiles.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                      </select>
                      <ChevronDown size={10} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                    </div>
                    {/* Student select */}
                    <div className="relative">
                      <select
                        value={adaptingId === a.id ? selectedStudent : ""}
                        onChange={(e) => { setAdaptingId(a.id); setSelectedStudent(e.target.value); }}
                        className="text-xs border border-gray-200 rounded-lg pl-2 pr-6 py-1.5 max-w-[130px] appearance-none"
                        title="Aluno destinatário"
                      >
                        <option value="">Sem aluno</option>
                        {students.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
                      </select>
                      <User size={10} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                    </div>
                    <button
                      onClick={() => handleAdapt(a.id)}
                      className="flex items-center gap-1.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg whitespace-nowrap"
                    >
                      <Sparkles size={12} /> Adaptar
                    </button>
                  </div>
                  {adaptingId === a.id && selectedStudent && (
                    <p className="text-xs text-green-600">
                      <User size={10} className="inline mr-0.5" />
                      {students.find((s) => s.id === selectedStudent)?.name}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create modal */}
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
                <label className="block text-xs font-medium text-gray-600 mb-1">Objetivo pedagógico</label>
                <input value={form.pedagogical_objective}
                  onChange={(e) => setForm({ ...form, pedagogical_objective: e.target.value })}
                  placeholder="Ex: Reconhecer animais aquáticos e terrestres"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
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
                  rows={2} placeholder="Contexto / texto base da atividade"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Pergunta</label>
                <input value={form.question} onChange={(e) => setForm({ ...form, question: e.target.value })}
                  placeholder="Ex: Classifique os animais em aquáticos ou terrestres"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Resposta esperada
                  <span className="ml-1 font-normal text-gray-400">(separe os itens por vírgula)</span>
                </label>
                <textarea value={form.expected_answer} onChange={(e) => setForm({ ...form, expected_answer: e.target.value })}
                  rows={2}
                  placeholder="Ex: Peixe, Tubarão, Golfinho são aquáticos. Leão, Elefante, Girafa são terrestres."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none" />
                <p className="text-xs text-gray-400 mt-1">
                  O agente usa os itens separados por vírgula para montar a atividade interativa.
                </p>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Observações para o agente</label>
                <textarea value={form.teacher_notes} onChange={(e) => setForm({ ...form, teacher_notes: e.target.value })}
                  rows={2} placeholder="Instruções específicas, contexto adicional, adaptações necessárias..."
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none" />
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
