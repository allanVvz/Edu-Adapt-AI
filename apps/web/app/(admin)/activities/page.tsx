"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AdminLayout from "@/components/layout/AdminLayout";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import toast from "react-hot-toast";
import {
  Plus, BookOpen, Sparkles, Search, ChevronDown, ChevronRight,
  Pencil, Check, X, ExternalLink,
} from "lucide-react";
import clsx from "clsx";

interface Activity {
  id: string;
  story_id?: string | null;
  story?: StorySummary | null;
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
interface StorySummary { id: string; title: string; status?: string }
interface Story extends StorySummary { content: string }

interface Adaptation {
  id: string;
  profile: { id: string; name: string } | null;
  status: string;
  version: number;
  generated_by: string;
  created_at: string;
}

const TYPE_LABEL: Record<string, string> = {
  multiple_choice: "Múltipla escolha", essay: "Dissertativa",
  association: "Associação", drag_drop: "Arrastar e soltar", game: "Brincadeira",
};
const STATUS_LABEL: Record<string, string> = {
  review: "Em revisão", approved: "Aprovado",
  published: "Publicado", rejected: "Reprovado", draft: "Rascunho",
};
const STATUS_FILTERS = [
  { value: "", label: "Todas" }, { value: "active", label: "Ativas" },
  { value: "draft", label: "Rascunho" }, { value: "archived", label: "Arquivadas" },
];
const EMPTY_FORM = {
  title: "", discipline: "", school_year: "",
  pedagogical_objective: "", teacher_notes: "",
  activity_type: "association", statement: "", question: "", expected_answer: "",
  base_complexity: 2, original_modality: "association",
  story_id: "", new_story_title: "", new_story_content: "",
};

export default function ActivitiesPage() {
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [stories, setStories] = useState<Story[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ ...EMPTY_FORM });
  const [saving, setSaving] = useState(false);

  // Accordion state
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editFields, setEditFields] = useState<Partial<typeof EMPTY_FORM>>({});
  const [savingEdit, setSavingEdit] = useState(false);

  // Per-activity adaptations
  const [actAdaptations, setActAdaptations] = useState<Record<string, Adaptation[]>>({});
  const [loadingAdapt, setLoadingAdapt] = useState<Record<string, boolean>>({});

  // Per-activity adapt action
  const [adaptingProfile, setAdaptingProfile] = useState<Record<string, string>>({});
  const [generatingAdapt, setGeneratingAdapt] = useState<string | null>(null);

  useEffect(() => {
    const user = getUser();
    setIsAdmin(user?.role === "admin");
    load();
  }, []);

  async function load(status?: string) {
    const params = status ? `?status=${status}` : "";
    const [a, p] = await Promise.all([
      api.get(`/activities${params}`).catch(() => ({ data: [] })),
      api.get("/student-profiles").catch(() => ({ data: [] })),
    ]);
    setActivities(a.data);
    setProfiles(p.data);
    api.get("/stories?status=active")
      .then((r) => setStories(r.data))
      .catch(() => setStories([]));
  }

  function handleFilterChange(status: string) {
    setStatusFilter(status);
    load(status);
  }

  const filtered = activities.filter((a) =>
    a.title.toLowerCase().includes(search.toLowerCase()) ||
    (a.discipline ?? "").toLowerCase().includes(search.toLowerCase())
  );

  async function loadActivityAdaptations(activityId: string) {
    if (actAdaptations[activityId] !== undefined) return;
    setLoadingAdapt((p) => ({ ...p, [activityId]: true }));
    try {
      const { data } = await api.get("/adaptations");
      const mine = (data as Adaptation[]).filter(
        (a: Adaptation & { activity?: { id: string } }) => a.activity?.id === activityId
      );
      setActAdaptations((p) => ({ ...p, [activityId]: mine }));
    } catch {
      setActAdaptations((p) => ({ ...p, [activityId]: [] }));
    } finally {
      setLoadingAdapt((p) => ({ ...p, [activityId]: false }));
    }
  }

  function toggleExpand(activityId: string) {
    if (expandedId === activityId) {
      setExpandedId(null);
      setEditingId(null);
    } else {
      setExpandedId(activityId);
      setEditingId(null);
      loadActivityAdaptations(activityId);
    }
  }

  function startInlineEdit(activity: Activity) {
    const full = activities.find((a) => a.id === activity.id);
    setEditingId(activity.id);
    setEditFields({
      title: full?.title || "",
      discipline: full?.discipline || "",
      school_year: full?.school_year || "",
      statement: "",
      question: "",
      expected_answer: "",
      teacher_notes: "",
      story_id: full?.story_id || "",
    });
    // Load full activity for editable fields
    api.get(`/activities/${activity.id}`).then((r) => {
      setEditFields({
        title: r.data.title || "",
        discipline: r.data.discipline || "",
        school_year: r.data.school_year || "",
        statement: r.data.statement || "",
        question: r.data.question || "",
        expected_answer: r.data.expected_answer || "",
        teacher_notes: r.data.teacher_notes || "",
        story_id: r.data.story_id || "",
      });
    }).catch(() => {});
  }

  async function saveInlineEdit(activityId: string) {
    setSavingEdit(true);
    try {
      const activityEditFields = { ...editFields };
      delete activityEditFields.new_story_title;
      delete activityEditFields.new_story_content;
      await api.put(`/activities/${activityId}`, {
        ...activityEditFields,
        story_id: activityEditFields.story_id || null,
        activity_type: activities.find((a) => a.id === activityId)?.activity_type || "association",
        base_complexity: activities.find((a) => a.id === activityId)?.base_complexity || 2,
        original_modality: "association",
      });
      toast.success("Atividade atualizada.");
      setEditingId(null);
      load(statusFilter);
    } catch {
      toast.error("Erro ao salvar.");
    } finally {
      setSavingEdit(false);
    }
  }

  async function handleAdapt(activityId: string) {
    const profileId = adaptingProfile[activityId] || "";
    if (!profileId) {
      toast.error("Selecione um perfil primeiro.");
      return;
    }
    setGeneratingAdapt(activityId);
    try {
      toast.loading("Gerando adaptação...", { id: "adapt" });
      const { data } = await api.post(`/activities/${activityId}/adapt`, {
        profile_id: profileId,
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
    } finally {
      setGeneratingAdapt(null);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      let storyId = form.story_id || null;
      if ((form.new_story_title.trim() || form.new_story_content.trim()) && !(form.new_story_title.trim() && form.new_story_content.trim())) {
        toast.error("Informe título e texto para criar um novo conto.");
        return;
      }
      if (form.new_story_title.trim() && form.new_story_content.trim()) {
        const { data } = await api.post("/stories", {
          title: form.new_story_title.trim(),
          content: form.new_story_content.trim(),
          image_options: [
            { id: "story_img_1", description: "personagem", illustration_type: "emoji", active_style: "pictogram", is_active: true, image_url: null, emoji: "📖" },
          ],
          audio_options: [
            { id: "story_audio_1", script: form.new_story_content.trim(), tts_script: form.new_story_content.trim(), voice_style: "calma", voice: "shimmer", rhythm: 0.85, pitch: "normal", audio_url: null, source: "teacher" },
          ],
        });
        storyId = data.id;
      }
      const activityPayload = {
        title: form.title,
        discipline: form.discipline,
        school_year: form.school_year,
        pedagogical_objective: form.pedagogical_objective,
        teacher_notes: form.teacher_notes,
        activity_type: form.activity_type,
        statement: form.statement,
        question: form.question,
        expected_answer: form.expected_answer,
        base_complexity: form.base_complexity,
        original_modality: form.original_modality,
      };
      await api.post("/activities", { ...activityPayload, story_id: storyId });
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

  function getActivityAdaptationsForProfile(activityId: string, profileId: string): Adaptation[] {
    return (actAdaptations[activityId] || []).filter(
      (a) => a.profile?.id === profileId
    );
  }

  return (
    <AdminLayout>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-gray-900">Atividades</h1>
        <button onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg">
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
        <div className="grid gap-2">
          {filtered.map((a) => {
            const isExpanded = expandedId === a.id;
            const isEditing = editingId === a.id;
            const isGenerating = generatingAdapt === a.id;

            return (
              <div key={a.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                {/* Card header — click to expand */}
                <button
                  onClick={() => toggleExpand(a.id)}
                  className="w-full text-left p-4 flex items-start gap-3 hover:bg-gray-50 transition-colors"
                >
                  <div className={clsx("mt-1 transition-transform", isExpanded ? "rotate-90" : "")}>
                    <ChevronRight size={16} className="text-gray-400" />
                  </div>
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
                      {a.story && <span className="text-xs bg-amber-50 text-amber-700 rounded-full px-2 py-0.5">Conto: {a.story.title}</span>}
                      <span className={clsx("text-xs rounded-full px-2 py-0.5", {
                        "bg-green-50 text-green-700": a.status === "active",
                        "bg-gray-100 text-gray-500": a.status === "draft",
                        "bg-red-50 text-red-500": a.status === "archived",
                      })}>
                        {a.status === "active" ? "Ativa" : a.status === "draft" ? "Rascunho" : "Arquivada"}
                      </span>
                    </div>
                  </div>
                  <div className="text-right flex-shrink-0">
                    {a.adaptation_total > 0 && (
                      <span className="text-xs text-gray-400">{a.adaptation_total} adaptação{a.adaptation_total !== 1 ? "ões" : ""}</span>
                    )}
                  </div>
                </button>

                {/* Accordion body */}
                {isExpanded && (
                  <div className="border-t border-gray-100 px-5 py-4 bg-gray-50">

                    {/* Inline edit section */}
                    {!isEditing ? (
                      <div className="mb-4 flex items-center justify-between">
                        <p className="text-xs text-gray-500">Conteúdo da atividade original</p>
                        <button onClick={() => startInlineEdit(a)}
                          className="flex items-center gap-1.5 text-xs text-blue-600 hover:text-blue-800 font-medium">
                          <Pencil size={12} /> Editar
                        </button>
                      </div>
                    ) : (
                      <div className="mb-4 bg-white rounded-xl border border-blue-200 p-4">
                        <div className="flex items-center justify-between mb-3">
                          <p className="text-sm font-medium text-gray-700">Editando atividade</p>
                          <div className="flex gap-2">
                            <button onClick={() => saveInlineEdit(a.id)} disabled={savingEdit}
                              className="flex items-center gap-1 text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg font-medium">
                              <Check size={11} /> {savingEdit ? "Salvando..." : "Salvar"}
                            </button>
                            <button onClick={() => setEditingId(null)}
                              className="flex items-center gap-1 text-xs border border-gray-300 text-gray-600 px-3 py-1.5 rounded-lg">
                              <X size={11} /> Cancelar
                            </button>
                          </div>
                        </div>
                        <div className="space-y-3">
                          {[
                            { label: "Título", key: "title" },
                            { label: "Disciplina", key: "discipline" },
                            { label: "Ano", key: "school_year" },
                          ].map(({ label, key }) => (
                            <div key={key} className="grid grid-cols-3 gap-2 items-center">
                              <label className="text-xs font-medium text-gray-500">{label}</label>
                              <input
                                className="col-span-2 border border-gray-200 rounded-lg px-3 py-1.5 text-sm"
                                value={(editFields as Record<string, string>)[key] || ""}
                                onChange={(e) => setEditFields({ ...editFields, [key]: e.target.value })}
                              />
                            </div>
                          ))}
                          <div className="grid grid-cols-3 gap-2 items-center">
                            <label className="text-xs font-medium text-gray-500">Conto vinculado</label>
                            <select
                              className="col-span-2 border border-gray-200 rounded-lg px-3 py-1.5 text-sm bg-white"
                              value={(editFields as Record<string, string>).story_id || ""}
                              onChange={(e) => setEditFields({ ...editFields, story_id: e.target.value })}
                            >
                              <option value="">Sem conto</option>
                              {stories.map((story) => (
                                <option key={story.id} value={story.id}>{story.title}</option>
                              ))}
                            </select>
                          </div>
                          {[
                            { label: "Enunciado", key: "statement" },
                            { label: "Pergunta", key: "question" },
                            { label: "Resposta esperada", key: "expected_answer" },
                            { label: "Observações", key: "teacher_notes" },
                          ].map(({ label, key }) => (
                            <div key={key}>
                              <label className="text-xs font-medium text-gray-500 block mb-1">{label}</label>
                              <textarea
                                rows={2}
                                className="w-full border border-gray-200 rounded-lg px-3 py-1.5 text-sm resize-none"
                                value={(editFields as Record<string, string>)[key] || ""}
                                onChange={(e) => setEditFields({ ...editFields, [key]: e.target.value })}
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Per-profile adapt section */}
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Adaptar por perfil</p>

                      {profiles.length === 0 ? (
                        <p className="text-xs text-gray-400">Nenhum perfil cadastrado.</p>
                      ) : (
                        <div className="space-y-3">
                          {profiles.map((profile) => {
                            const existingAdaptations = getActivityAdaptationsForProfile(a.id, profile.id);
                            const isLoadingThisActivity = loadingAdapt[a.id];

                            return (
                              <div key={profile.id} className="bg-white rounded-xl border border-gray-200 p-3">
                                <div className="flex items-center justify-between mb-2">
                                  <p className="text-sm font-medium text-gray-800">{profile.name}</p>
                                  <div className="flex items-center gap-2">
                                    {adaptingProfile[a.id] === profile.id ? (
                                      <button
                                        onClick={() => handleAdapt(a.id)}
                                        disabled={isGenerating}
                                        className="flex items-center gap-1.5 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-1.5 rounded-lg"
                                      >
                                        <Sparkles size={11} />
                                        {isGenerating ? "Gerando..." : "Gerar adaptação"}
                                      </button>
                                    ) : (
                                      <button
                                        onClick={() => setAdaptingProfile({ ...adaptingProfile, [a.id]: profile.id })}
                                        className="flex items-center gap-1 text-xs text-purple-600 hover:text-purple-800 border border-purple-200 hover:border-purple-400 px-3 py-1.5 rounded-lg font-medium"
                                      >
                                        <Sparkles size={11} /> Adaptar
                                      </button>
                                    )}
                                  </div>
                                </div>

                                {/* Existing adaptations for this profile */}
                                {isLoadingThisActivity ? (
                                  <p className="text-xs text-gray-400">Carregando...</p>
                                ) : existingAdaptations.length > 0 ? (
                                  <div className="flex flex-wrap gap-1.5 mt-1">
                                    {existingAdaptations.map((adapt) => (
                                      <button
                                        key={adapt.id}
                                        onClick={() => router.push(`/adaptations/${adapt.id}/review`)}
                                        className={clsx(
                                          "flex items-center gap-1 text-xs rounded-full px-2.5 py-1 border font-medium hover:shadow-sm transition-all",
                                          {
                                            "bg-yellow-50 text-yellow-700 border-yellow-200": adapt.status === "review",
                                            "bg-green-50 text-green-700 border-green-200": adapt.status === "approved" || adapt.status === "published",
                                            "bg-red-50 text-red-600 border-red-200": adapt.status === "rejected",
                                            "bg-gray-100 text-gray-500 border-gray-200": adapt.status === "draft",
                                          }
                                        )}
                                      >
                                        {STATUS_LABEL[adapt.status] || adapt.status} v{adapt.version}
                                        <ExternalLink size={9} />
                                      </button>
                                    ))}
                                  </div>
                                ) : (
                                  <p className="text-xs text-gray-400 mt-1">Sem adaptações para este perfil.</p>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Create modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold text-gray-900">Nova atividade</h2>
              <button onClick={() => setShowModal(false)} className="p-1.5 hover:bg-gray-100 rounded-lg">
                <X size={16} className="text-gray-500" />
              </button>
            </div>
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
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm" />
              </div>
              <div className="rounded-xl border border-amber-100 bg-amber-50/40 p-3 space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Conto vinculado</label>
                  <select
                    value={form.story_id}
                    onChange={(e) => setForm({ ...form, story_id: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white"
                  >
                    <option value="">Sem conto</option>
                    {stories.map((story) => (
                      <option key={story.id} value={story.id}>{story.title}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">Criar novo conto nesta atividade</label>
                  <input
                    value={form.new_story_title}
                    onChange={(e) => setForm({ ...form, new_story_title: e.target.value })}
                    placeholder="Título do conto"
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white mb-2"
                  />
                  <textarea
                    value={form.new_story_content}
                    onChange={(e) => setForm({ ...form, new_story_content: e.target.value })}
                    placeholder="Texto do conto"
                    rows={3}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm bg-white resize-none"
                  />
                  <p className="text-[11px] text-gray-500 mt-1">Se preencher título e texto, o novo conto será usado no lugar do conto selecionado.</p>
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
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Resposta esperada <span className="font-normal text-gray-400">(sep. por vírgula)</span>
                </label>
                <textarea value={form.expected_answer} onChange={(e) => setForm({ ...form, expected_answer: e.target.value })}
                  rows={2} className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Observações para o agente</label>
                <textarea value={form.teacher_notes} onChange={(e) => setForm({ ...form, teacher_notes: e.target.value })}
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
