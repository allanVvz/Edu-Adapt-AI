"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AdminLayout from "@/components/layout/AdminLayout";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import toast from "react-hot-toast";
import {
  CheckCircle, XCircle, RefreshCw, Send, UserCheck,
  ChevronDown, Loader2, Play,
} from "lucide-react";
import clsx from "clsx";

const TABS = ["Texto", "Visual", "Imagens", "Áudio", "Interação", "Impressão", "Executar", "Validação"] as const;
type Tab = (typeof TABS)[number];

// Item can be string or {name, image}
type ActivityItem = string | { name: string; image?: string };
type ActivityZone = string | { name: string };
const label = (v: ActivityItem | ActivityZone): string =>
  typeof v === "string" ? v : v.name;

interface AdaptationData {
  id: string;
  activity: {
    id: string;
    title: string;
    teacher_id: string | null;
    teacher_name: string | null;
  } | null;
  profile: { id: string; name: string } | null;
  student_id: string | null;
  student_name: string | null;
  generated_by: string;
  status: string;
  version: number;
  output: Record<string, unknown>;
  validator_feedback: string | null;
  teacher_feedback: string | null;
}

interface StudentItem { id: string; name: string; email: string }
interface TeacherItem { id: string; name: string; email: string; role: string }

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [data, setData] = useState<AdaptationData | null>(null);
  const [tab, setTab] = useState<Tab>("Texto");
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);

  // Assignment state
  const [students, setStudents] = useState<StudentItem[]>([]);
  const [teachers, setTeachers] = useState<TeacherItem[]>([]);
  const [assignStudentId, setAssignStudentId] = useState("");
  const [assignTeacherId, setAssignTeacherId] = useState("");
  const [savingAssign, setSavingAssign] = useState(false);

  // Execute preview state
  const [previewAnswers, setPreviewAnswers] = useState<Record<string, string>>({});

  useEffect(() => {
    const user = getUser();
    const admin = user?.role === "admin";
    setIsAdmin(admin);
    load();
    if (admin) {
      api.get("/students").then((r) => setStudents(r.data)).catch(() => {});
      api.get("/admin/users").then((r) =>
        setTeachers((r.data as TeacherItem[]).filter((u) => u.role === "teacher" || u.role === "admin"))
      ).catch(() => {});
    }
  }, [id]);

  async function load() {
    try {
      const { data: d } = await api.get(`/adaptations/${id}`);
      setData(d);
      setAssignStudentId(d.student_id || "");
      setAssignTeacherId(d.activity?.teacher_id || "");
    } catch {
      toast.error("Adaptação não encontrada.");
      router.push("/validations");
    }
  }

  async function handle(action: "approve" | "reject" | "reprocess" | "publish") {
    setLoading(true);
    try {
      if (action === "approve") {
        await api.post(`/adaptations/${id}/approve`);
        toast.success("Adaptação aprovada.");
      } else if (action === "reject") {
        await api.post(`/adaptations/${id}/reject`, { feedback });
        toast.success("Adaptação reprovada.");
      } else if (action === "reprocess") {
        const { data: r } = await api.post(`/adaptations/${id}/reprocess`, { feedback });
        toast.success("Reprocessando...");
        router.push(`/adaptations/${r.id}/review`);
        return;
      } else if (action === "publish") {
        await api.post(`/adaptations/${id}/publish`);
        toast.success("Adaptação publicada para o aluno.");
      }
      load();
    } catch {
      toast.error("Erro ao processar ação.");
    } finally {
      setLoading(false);
    }
  }

  async function saveAssignment(andPublish = false) {
    setSavingAssign(true);
    try {
      await api.put(`/admin/adaptations/${id}/assign`, {
        student_id: assignStudentId || null,
        teacher_id: assignTeacherId || null,
      });
      if (andPublish) {
        await api.post(`/adaptations/${id}/publish`);
        toast.success("Atribuições salvas e adaptação publicada!");
      } else {
        toast.success("Atribuições salvas.");
      }
      load();
    } catch {
      toast.error("Erro ao salvar atribuições.");
    } finally {
      setSavingAssign(false);
    }
  }

  if (!data) return (
    <AdminLayout>
      <div className="flex justify-center py-20">
        <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    </AdminLayout>
  );

  const output = data.output || {};
  const textAdaptations = (output.text_adaptations as Array<{ version: number; content: string }>) || [];
  const imageOptions = (output.image_options as Array<{ id: string; description: string; prompt: string }>) || [];
  const audioOptions = (output.audio_options as Array<{ id?: string; script: string; voice_style: string }>) || [];
  const interactionOptions = (output.interaction_options as Array<{
    type: string;
    instructions: string;
    items: ActivityItem[];
    zones: ActivityZone[];
    feedback_correct?: string;
    feedback_incorrect?: string;
  }>) || [];
  const visualModality = output.visual_modality as { type: string; instructions: string } | undefined;
  const printVersion = (output.print_version as Record<string, unknown>) || {};
  const validation = output.validation as {
    clarity_score: number;
    accessibility_score: number;
    pedagogical_score: number;
    approved: boolean;
    notes: string;
  } | undefined;

  // For execute preview
  const previewInteraction = interactionOptions[0];
  const previewText = textAdaptations[0]?.content;
  const previewAudio = audioOptions[0];

  return (
    <AdminLayout>
      {/* Header */}
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            {data.activity?.title || "Adaptação"} — v{data.version}
          </h1>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            {data.profile && (
              <span className="text-xs bg-purple-100 text-purple-700 rounded-full px-2 py-0.5">{data.profile.name}</span>
            )}
            {data.activity?.teacher_name && (
              <span className="text-xs bg-orange-50 text-orange-600 border border-orange-100 rounded-full px-2 py-0.5">
                Prof. {data.activity.teacher_name}
              </span>
            )}
            {data.student_name ? (
              <span className="text-xs bg-green-50 text-green-700 border border-green-100 rounded-full px-2 py-0.5">
                Aluno: {data.student_name}
              </span>
            ) : (
              <span className="text-xs bg-gray-100 text-gray-400 rounded-full px-2 py-0.5">Sem aluno atribuído</span>
            )}
            <span className={clsx("text-xs rounded-full px-2 py-0.5 font-medium", {
              "bg-yellow-100 text-yellow-700": data.status === "review",
              "bg-green-100 text-green-700": data.status === "approved" || data.status === "published",
              "bg-red-100 text-red-700": data.status === "rejected",
              "bg-gray-100 text-gray-500": data.status === "draft",
            })}>
              {data.status}
            </span>
            <span className="text-xs text-gray-400">via {data.generated_by}</span>
          </div>
        </div>

        <div className="flex gap-2 flex-wrap">
          {data.status !== "published" && (
            <>
              <button onClick={() => handle("approve")} disabled={loading}
                className="flex items-center gap-1.5 bg-green-600 hover:bg-green-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                <CheckCircle size={13} /> Aprovar
              </button>
              <button onClick={() => handle("publish")} disabled={loading}
                className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium px-3 py-1.5 rounded-lg">
                <Send size={13} /> Publicar
              </button>
            </>
          )}
          <button onClick={() => handle("reject")} disabled={loading}
            className="flex items-center gap-1.5 border border-red-200 text-red-600 hover:bg-red-50 text-xs font-medium px-3 py-1.5 rounded-lg">
            <XCircle size={13} /> Reprovar
          </button>
          <button onClick={() => handle("reprocess")} disabled={loading}
            className="flex items-center gap-1.5 border border-gray-200 text-gray-600 hover:bg-gray-50 text-xs font-medium px-3 py-1.5 rounded-lg">
            <RefreshCw size={13} /> Regerar
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 overflow-x-auto pb-1">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={clsx("px-4 py-2 text-sm font-medium rounded-lg whitespace-nowrap transition-colors", {
              "bg-blue-600 text-white": tab === t,
              "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50": tab !== t,
            })}>
            {t === "Executar" && <Play size={12} className="inline mr-1.5 -mt-0.5" />}
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="bg-white rounded-xl border border-gray-200 p-6 min-h-[300px]">
        {tab === "Texto" && (
          <div>
            <h2 className="font-semibold text-gray-700 mb-3">Texto adaptado</h2>
            {textAdaptations.length === 0 ? (
              <p className="text-gray-400 text-sm">Nenhuma adaptação de texto gerada.</p>
            ) : textAdaptations.map((t) => (
              <div key={t.version} className="bg-gray-50 rounded-lg p-4 mb-3">
                <p className="text-xs text-gray-400 mb-2">Versão {t.version}</p>
                <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans">{t.content}</pre>
              </div>
            ))}
          </div>
        )}

        {tab === "Imagens" && (
          <div>
            <h2 className="font-semibold text-gray-700 mb-3">Opções de imagem</h2>
            {imageOptions.length === 0 ? (
              <p className="text-gray-400 text-sm">Nenhuma opção de imagem.</p>
            ) : (
              <div className="grid gap-3">
                {imageOptions.map((img) => (
                  <div key={img.id} className="border border-gray-200 rounded-lg p-4">
                    <p className="font-medium text-sm text-gray-800 mb-1">{img.description}</p>
                    <p className="text-xs text-gray-400 font-mono bg-gray-50 p-2 rounded">{img.prompt}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === "Áudio" && (
          <div>
            <h2 className="font-semibold text-gray-700 mb-3">Roteiros de áudio</h2>
            {audioOptions.length === 0 ? (
              <p className="text-gray-400 text-sm">Nenhum roteiro de áudio.</p>
            ) : audioOptions.map((a, i) => (
              <div key={a.id ?? i} className="bg-gray-50 rounded-lg p-4 mb-3">
                <p className="text-xs text-gray-400 mb-1">Estilo: <span className="text-gray-600">{a.voice_style}</span></p>
                <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans">{a.script}</pre>
              </div>
            ))}
          </div>
        )}

        {tab === "Interação" && (
          <div>
            <h2 className="font-semibold text-gray-700 mb-3">Atividade interativa</h2>
            {interactionOptions.length === 0 ? (
              <p className="text-gray-400 text-sm">Nenhuma opção de interação.</p>
            ) : interactionOptions.map((i, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-4 mb-3">
                <p className="font-medium text-sm text-gray-800 mb-2">{i.instructions}</p>
                <p className="text-xs text-gray-500 mb-1">Tipo: {i.type}</p>
                <div className="flex flex-wrap gap-2 mb-2">
                  {i.items?.map((item, j) => (
                    <span key={j} className="bg-blue-100 text-blue-700 text-xs rounded-full px-2 py-0.5">{label(item)}</span>
                  ))}
                </div>
                <p className="text-xs text-gray-500">
                  Zonas: {i.zones?.map(label).join(", ")}
                </p>
              </div>
            ))}
          </div>
        )}

        {tab === "Visual" && (
          <div>
            <h2 className="font-semibold text-gray-700 mb-3">Modalidade visual</h2>
            {!visualModality ? (
              <p className="text-gray-400 text-sm">Nenhuma estrutura visual gerada.</p>
            ) : (
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm font-medium text-gray-700">{visualModality.instructions}</p>
                <p className="text-xs text-gray-400 mt-1">Tipo: {visualModality.type}</p>
              </div>
            )}
          </div>
        )}

        {tab === "Impressão" && (
          <div>
            <h2 className="font-semibold text-gray-700 mb-3">Versão para impressão</h2>
            {Object.keys(printVersion).length === 0 ? (
              <p className="text-gray-400 text-sm">Nenhuma versão de impressão.</p>
            ) : (
              <div className="border-2 border-dashed border-gray-200 rounded-xl p-6 bg-white">
                <div className="text-center mb-4">
                  <p className="font-bold text-lg">{data.activity?.title}</p>
                  <p className="text-sm text-gray-500">{String(printVersion.instructions || "")}</p>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="border border-gray-200 rounded-lg p-4 min-h-24 text-center text-gray-400 text-sm">Zona A</div>
                  <div className="border border-gray-200 rounded-lg p-4 min-h-24 text-center text-gray-400 text-sm">Zona B</div>
                </div>
                <div className="mt-4 border-t pt-3">
                  <p className="text-xs text-gray-400">Formato: {String(printVersion.format || "A4")} — Fonte: {String(printVersion.font_size || "large")}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Execute preview tab ── */}
        {tab === "Executar" && (
          <div>
            <div className="flex items-center gap-2 mb-4">
              <h2 className="font-semibold text-gray-700">Pré-visualização — como o aluno vê</h2>
              <span className="text-xs bg-amber-50 text-amber-600 border border-amber-100 rounded-full px-2 py-0.5">
                somente visualização, sem envio
              </span>
            </div>

            {previewText && (
              <div className="bg-white border border-blue-100 rounded-2xl p-6 mb-4">
                <pre className="text-base text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">{previewText}</pre>
              </div>
            )}

            {previewAudio && (
              <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-4 flex items-start gap-3">
                <div>
                  <p className="text-xs text-blue-500 font-medium mb-1">Áudio — {previewAudio.voice_style}</p>
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{previewAudio.script}</pre>
                </div>
              </div>
            )}

            {previewInteraction ? (
              <div className="bg-white border border-blue-100 rounded-2xl p-6">
                <p className="font-bold text-gray-900 text-center mb-4 text-lg">{previewInteraction.instructions}</p>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  {previewInteraction.zones?.map((zone) => {
                    const zoneLabel = label(zone);
                    return (
                      <div key={zoneLabel} className="border-2 border-dashed border-blue-200 rounded-xl p-3 min-h-28">
                        <p className="text-center font-semibold text-blue-600 mb-2 text-sm">{zoneLabel}</p>
                        <div className="space-y-1.5">
                          {previewInteraction.items?.filter((item) => previewAnswers[label(item)] === zoneLabel).map((item) => (
                            <div key={label(item)} className="bg-blue-100 text-blue-800 text-sm font-medium rounded-lg px-3 py-1.5 text-center">
                              {label(item)}
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="flex flex-wrap gap-2 justify-center mb-4">
                  {previewInteraction.items?.filter((item) => !previewAnswers[label(item)]).map((item) => {
                    const itemLabel = label(item);
                    return (
                      <div key={itemLabel}>
                        <div className="flex gap-1 flex-wrap justify-center">
                          {previewInteraction.zones?.map((zone) => {
                            const zoneLabel = label(zone);
                            return (
                              <button key={zoneLabel}
                                onClick={() => setPreviewAnswers((p) => ({ ...p, [itemLabel]: zoneLabel }))}
                                className="bg-white border border-gray-300 hover:border-blue-400 hover:bg-blue-50 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 transition-colors">
                                {itemLabel} → {zoneLabel}
                              </button>
                            );
                          })}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {Object.keys(previewAnswers).length > 0 && (
                  <button onClick={() => setPreviewAnswers({})}
                    className="w-full border border-gray-200 text-gray-500 text-sm py-2 rounded-xl">
                    Recomeçar pré-visualização
                  </button>
                )}

                <p className="text-center text-xs text-gray-400 mt-3">
                  O botão de envio aparece para o aluno após responder todos os itens.
                </p>
              </div>
            ) : (
              !previewText && !previewAudio && (
                <p className="text-gray-400 text-sm">Nenhum conteúdo disponível para pré-visualização.</p>
              )
            )}
          </div>
        )}

        {tab === "Validação" && (
          <div>
            <h2 className="font-semibold text-gray-700 mb-3">Relatório do validador</h2>
            {!validation ? (
              <p className="text-gray-400 text-sm">Nenhuma validação disponível.</p>
            ) : (
              <div>
                <div className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium mb-4 ${validation.approved ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                  {validation.approved ? <CheckCircle size={14} /> : <XCircle size={14} />}
                  {validation.approved ? "Aprovado" : "Reprovado"}
                </div>
                <div className="grid grid-cols-2 gap-3 mb-4">
                  {[
                    { label: "Clareza", score: validation.clarity_score },
                    { label: "Acessibilidade", score: validation.accessibility_score },
                    { label: "Pedagógico", score: validation.pedagogical_score },
                  ].map(({ label: lbl, score }) => (
                    <div key={lbl} className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">{lbl}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-full bg-blue-500 rounded-full" style={{ width: `${(score / 5) * 100}%` }} />
                        </div>
                        <span className="text-sm font-bold text-gray-700">{score}/5</span>
                      </div>
                    </div>
                  ))}
                </div>
                {validation.notes && (
                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">{validation.notes}</p>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Feedback textarea */}
      <div className="mt-4 bg-white rounded-xl border border-gray-200 p-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">Feedback para reprocessamento / reprovação</label>
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          rows={2}
          placeholder="Descreva o que precisa ser melhorado..."
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none"
        />
      </div>

      {/* Assignment panel — admin only */}
      {isAdmin && (
        <div className="mt-4 bg-white rounded-xl border border-blue-100 p-4">
          <div className="flex items-center gap-2 mb-3">
            <UserCheck size={16} className="text-blue-500" />
            <h3 className="font-semibold text-gray-700 text-sm">Atribuições da adaptação</h3>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Professor responsável</label>
              <div className="relative">
                <select
                  value={assignTeacherId}
                  onChange={(e) => setAssignTeacherId(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm appearance-none pr-8"
                >
                  <option value="">Sem professor</option>
                  {teachers.map((t) => (
                    <option key={t.id} value={t.id}>{t.name} ({t.role})</option>
                  ))}
                </select>
                <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Aluno destinatário
                {!assignStudentId && data.profile && (
                  <span className="ml-1 text-purple-500">(distribuído por perfil: {data.profile.name})</span>
                )}
              </label>
              <div className="relative">
                <select
                  value={assignStudentId}
                  onChange={(e) => setAssignStudentId(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm appearance-none pr-8"
                >
                  <option value="">Sem aluno específico (por perfil)</option>
                  {students.map((s) => (
                    <option key={s.id} value={s.id}>{s.name} — {s.email}</option>
                  ))}
                </select>
                <ChevronDown size={12} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
              </div>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => saveAssignment(false)}
              disabled={savingAssign}
              className="flex items-center gap-1.5 border border-gray-200 text-gray-700 hover:bg-gray-50 text-xs font-medium px-3 py-2 rounded-lg"
            >
              {savingAssign ? <Loader2 size={12} className="animate-spin" /> : <UserCheck size={12} />}
              Salvar atribuições
            </button>
            <button
              onClick={() => saveAssignment(true)}
              disabled={savingAssign || data.status === "published"}
              className="flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-xs font-medium px-3 py-2 rounded-lg"
            >
              {savingAssign ? <Loader2 size={12} className="animate-spin" /> : <Send size={12} />}
              Salvar + Publicar para aluno
            </button>
            {data.status === "published" && (
              <span className="text-xs text-green-600 flex items-center gap-1">
                <CheckCircle size={12} /> Publicado
              </span>
            )}
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
