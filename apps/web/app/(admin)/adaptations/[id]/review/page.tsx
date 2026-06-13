"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AdminLayout from "@/components/layout/AdminLayout";
import ImagePickerModal from "@/components/ImagePickerModal";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import toast from "react-hot-toast";
import {
  CheckCircle, XCircle, RefreshCw, Send, UserCheck,
  ChevronDown, Loader2, Play, ImageIcon, Images, RotateCcw,
} from "lucide-react";
import clsx from "clsx";

const TABS = ["Texto", "Visual", "Imagens", "Áudio", "Interação", "Impressão", "Executar", "Validação"] as const;
type Tab = (typeof TABS)[number];
type ImageStyle = "line_art" | "cartoon_2d";

const STYLE_LABELS: Record<ImageStyle, string> = {
  line_art: "Desenho P&B — traços simples",
  cartoon_2d: "Cartoon colorido — detalhes 2D",
};

type ActivityItem = string | { name: string; image?: string };
type ActivityZone = string | { name: string };
const label = (v: ActivityItem | ActivityZone): string => {
  if (typeof v === "string") return v;
  return v.name || (v as Record<string, string>).description || "";
};

interface ImageOption {
  id: string;
  description: string;
  base_subject?: string;
  prompts?: Record<ImageStyle, string>;
  generated?: Record<ImageStyle, { image_url: string | null; generated_at?: string | null }>;
  active_style?: ImageStyle;
  is_active?: boolean;
  image_url?: string | null;
  prompt?: string;
}

interface AdaptationData {
  id: string;
  activity: { id: string; title: string; teacher_id: string | null; teacher_name: string | null } | null;
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

// A slot reference used for picker + regen
interface SlotRef {
  slot_type: "image_option" | "interaction_item";
  slot_id: string;
  current_url?: string | null;
}

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [data, setData] = useState<AdaptationData | null>(null);
  const [tab, setTab] = useState<Tab>("Texto");
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);

  // Image management
  const [activeStyle, setActiveStyle] = useState<ImageStyle>("cartoon_2d");
  const [generatingStyle, setGeneratingStyle] = useState<ImageStyle | null>(null);
  const [applyingStyle, setApplyingStyle] = useState(false);

  // Gallery picker
  const [pickerSlot, setPickerSlot] = useState<SlotRef | null>(null);
  const [applyingPick, setApplyingPick] = useState(false);

  // Per-image regeneration
  const [regenSlot, setRegenSlot] = useState<SlotRef | null>(null);
  const [regenFeedback, setRegenFeedback] = useState("");
  const [regenerating, setRegenerating] = useState(false);

  // Assignment
  const [students, setStudents] = useState<StudentItem[]>([]);
  const [teachers, setTeachers] = useState<TeacherItem[]>([]);
  const [assignStudentId, setAssignStudentId] = useState("");
  const [assignTeacherId, setAssignTeacherId] = useState("");
  const [savingAssign, setSavingAssign] = useState(false);

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
      const imgs = (d.output?.image_options as ImageOption[]) || [];
      const firstStyle = imgs[0]?.active_style;
      if (firstStyle) setActiveStyle(firstStyle);
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

  async function generateImagesForStyle(style: ImageStyle) {
    setGeneratingStyle(style);
    try {
      const result = await api.post(`/adaptations/${id}/generate-images`, { style });
      const errs = result.data?.errors ?? [];
      if (errs.length > 0) {
        const first = errs[0] as { error: string };
        toast.error(first.error, { duration: 10000 });
      } else {
        toast.success(`Imagens ${STYLE_LABELS[style]} geradas e salvas na galeria!`);
      }
      load();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Erro ao gerar imagens. Verifique sua chave OpenAI.");
    } finally {
      setGeneratingStyle(null);
    }
  }

  async function applyImageStyle() {
    setApplyingStyle(true);
    try {
      await api.post(`/adaptations/${id}/image-style`, {
        style: activeStyle,
        active_image_ids: imageOptions.map((img) => img.id),
      });
      toast.success(`Estilo "${STYLE_LABELS[activeStyle]}" aplicado!`);
      load();
    } catch {
      toast.error("Erro ao aplicar estilo.");
    } finally {
      setApplyingStyle(false);
    }
  }

  async function handlePickerSelect(imageUrl: string, _galleryImageId: string) {
    if (!pickerSlot) return;
    setApplyingPick(true);
    try {
      await api.post(`/adaptations/${id}/apply-gallery-image`, {
        slot_type: pickerSlot.slot_type,
        slot_id: pickerSlot.slot_id,
        image_url: imageUrl,
        gallery_image_id: _galleryImageId,
      });
      toast.success("Imagem substituída com sucesso!");
      load();
    } catch {
      toast.error("Erro ao substituir imagem.");
    } finally {
      setApplyingPick(false);
      setPickerSlot(null);
    }
  }

  async function handleRegenerate() {
    if (!regenSlot) return;
    setRegenerating(true);
    try {
      await api.post(`/adaptations/${id}/regenerate-image`, {
        slot_type: regenSlot.slot_type,
        slot_id: regenSlot.slot_id,
        style: activeStyle,
        feedback: regenFeedback,
      });
      toast.success("Nova imagem gerada e salva na galeria!");
      setRegenSlot(null);
      setRegenFeedback("");
      load();
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      toast.error(msg || "Erro ao regenerar imagem.");
    } finally {
      setRegenerating(false);
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
  const imageOptions = (output.image_options as ImageOption[]) || [];
  const audioOptions = (output.audio_options as Array<{ id?: string; script: string; voice_style: string }>) || [];
  const interactionOptions = (output.interaction_options as Array<{
    type: string; instructions: string;
    items: ActivityItem[]; zones: ActivityZone[];
    feedback_correct?: string; feedback_incorrect?: string;
  }>) || [];
  const printVersion = (output.print_version as Record<string, unknown>) || {};
  const validation = output.validation as {
    clarity_score: number; accessibility_score: number; pedagogical_score: number;
    approved: boolean; notes: string;
  } | undefined;

  const previewInteraction = interactionOptions[0];
  const previewText = textAdaptations[0]?.content;
  const previewAudio = audioOptions[0];

  const interactionItems = interactionOptions.flatMap((io) =>
    (io.items || []).filter((it) => typeof it !== "string" && (it as ImageOption).name)
      .map((it) => it as unknown as ImageOption & { name: string })
  );

  const visualImages = imageOptions.filter((img) => img.is_active && img.image_url);

  // Helper: renders image card with click-to-pick and regen controls
  function ImageCard({
    slotType, slotId, imageUrl, title, isSmall = false,
  }: {
    slotType: "image_option" | "interaction_item";
    slotId: string;
    imageUrl: string | null | undefined;
    title: string;
    isSmall?: boolean;
  }) {
    const isRegen = regenSlot?.slot_type === slotType && regenSlot?.slot_id === slotId;
    return (
      <div className="border border-gray-200 rounded-xl p-3 bg-white">
        {/* Thumbnail — click to open gallery picker */}
        <div
          className={clsx(
            "w-full rounded-lg overflow-hidden border border-gray-100 bg-gray-50 flex items-center justify-center mb-2 cursor-pointer group relative",
            isSmall ? "h-20" : "aspect-square"
          )}
          onClick={() => setPickerSlot({ slot_type: slotType, slot_id: slotId, current_url: imageUrl })}
          title="Clique para escolher outra imagem da galeria"
        >
          {imageUrl ? (
            <>
              <img src={imageUrl} alt={title} className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
                <div className="opacity-0 group-hover:opacity-100 transition-opacity bg-white/90 rounded-lg px-2 py-1 flex items-center gap-1 text-xs text-gray-700 font-medium">
                  <Images size={11} /> Trocar
                </div>
              </div>
            </>
          ) : (
            <div className="text-center text-gray-300 group-hover:text-blue-400 transition-colors">
              <ImageIcon size={isSmall ? 20 : 28} className="mx-auto" />
              <p className="text-xs mt-1">Escolher</p>
            </div>
          )}
        </div>

        <p className="text-xs font-medium text-gray-700 text-center">{title}</p>
        {imageUrl && <p className="text-xs text-green-600 text-center mt-0.5">✓ Gerado</p>}

        {/* Regen toggle */}
        {!isRegen ? (
          <button
            onClick={() => { setRegenSlot({ slot_type: slotType, slot_id: slotId }); setRegenFeedback(""); }}
            className="mt-2 w-full flex items-center justify-center gap-1 text-xs text-gray-500 hover:text-purple-600 border border-gray-200 hover:border-purple-300 rounded-lg py-1 transition-colors"
          >
            <RotateCcw size={10} /> Refazer
          </button>
        ) : (
          <div className="mt-2 space-y-1.5">
            <textarea
              value={regenFeedback}
              onChange={(e) => setRegenFeedback(e.target.value)}
              rows={2}
              placeholder="Ex: peixe visto de longe, ângulo distante, peixe menor na água..."
              className="w-full text-xs border border-purple-300 rounded-lg px-2 py-1.5 resize-none focus:outline-none focus:ring-1 focus:ring-purple-400"
              autoFocus
            />
            <div className="flex gap-1">
              <button
                onClick={handleRegenerate}
                disabled={regenerating}
                className="flex-1 flex items-center justify-center gap-1 text-xs bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white rounded-lg py-1.5 font-medium"
              >
                {regenerating ? <Loader2 size={10} className="animate-spin" /> : <RotateCcw size={10} />}
                {regenerating ? "Gerando..." : "Regenerar"}
              </button>
              <button
                onClick={() => setRegenSlot(null)}
                className="text-xs text-gray-400 hover:text-gray-600 px-2 border border-gray-200 rounded-lg"
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <AdminLayout>
      {/* Gallery picker modal */}
      <ImagePickerModal
        open={!!pickerSlot}
        onClose={() => setPickerSlot(null)}
        onSelect={handlePickerSelect}
        currentImageUrl={pickerSlot?.current_url}
      />

      {/* Applying overlay */}
      {applyingPick && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-black/20">
          <div className="bg-white rounded-xl px-6 py-4 shadow-lg flex items-center gap-3">
            <Loader2 size={18} className="animate-spin text-blue-600" />
            <p className="text-sm font-medium">Substituindo imagem...</p>
          </div>
        </div>
      )}

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

        {tab === "Visual" && (
          <div>
            <h2 className="font-semibold text-gray-700 mb-4">Imagens ativas — visão do aluno</h2>
            {visualImages.length === 0 ? (
              <div className="text-center py-10 text-gray-400 text-sm">
                <ImageIcon size={32} className="mx-auto mb-2 opacity-30" />
                <p>Nenhuma imagem ativa. Gere imagens na aba "Imagens" e clique em "Aplicar".</p>
              </div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {visualImages.map((img) => (
                  <div key={img.id} className="text-center">
                    <img
                      src={img.image_url!}
                      alt={img.description}
                      className="w-full aspect-square object-cover rounded-xl border border-gray-100 shadow-sm"
                    />
                    <p className="text-xs text-gray-600 mt-2 font-medium">{img.description}</p>
                    <p className="text-xs text-gray-400">{STYLE_LABELS[img.active_style ?? "cartoon_2d"]}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {tab === "Imagens" && (
          <div>
            {/* Style selector + Gerar buttons */}
            <div className="flex flex-wrap items-center gap-3 mb-5">
              <h2 className="font-semibold text-gray-700">Estilo:</h2>
              {(Object.keys(STYLE_LABELS) as ImageStyle[]).map((style) => (
                <div key={style} className="flex items-center gap-2">
                  <button
                    onClick={() => setActiveStyle(style)}
                    className={clsx(
                      "px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors",
                      activeStyle === style
                        ? "bg-purple-600 text-white border-purple-600"
                        : "bg-white text-gray-600 border-gray-200 hover:border-purple-300"
                    )}
                  >
                    {STYLE_LABELS[style]}
                  </button>
                  <button
                    onClick={() => generateImagesForStyle(style)}
                    disabled={!!generatingStyle}
                    className="flex items-center gap-1.5 bg-purple-50 hover:bg-purple-100 disabled:opacity-50 text-purple-700 text-xs font-medium px-3 py-1.5 rounded-lg border border-purple-200"
                  >
                    {generatingStyle === style ? <Loader2 size={11} className="animate-spin" /> : <ImageIcon size={11} />}
                    Gerar
                  </button>
                </div>
              ))}
              <div className="ml-auto">
                <p className="text-xs text-gray-400 flex items-center gap-1">
                  <Images size={11} /> Clique em uma imagem para trocar pela galeria
                </p>
              </div>
            </div>

            {imageOptions.length === 0 && interactionItems.length === 0 ? (
              <p className="text-gray-400 text-sm">Nenhuma imagem disponível. Regenere a adaptação.</p>
            ) : (
              <>
                {imageOptions.length > 0 && (
                  <div className="mb-6">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Imagens da atividade</p>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                      {imageOptions.map((img) => {
                        const generatedEntry = img.generated?.[activeStyle];
                        const imageUrl = generatedEntry?.image_url || img.image_url || null;
                        return (
                          <ImageCard
                            key={img.id}
                            slotType="image_option"
                            slotId={img.id}
                            imageUrl={imageUrl}
                            title={img.description}
                          />
                        );
                      })}
                    </div>
                  </div>
                )}

                {interactionItems.length > 0 && (
                  <div className="mb-6">
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">Itens da interação</p>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {interactionItems.map((item) => {
                        const generatedEntry = (item as unknown as ImageOption).generated?.[activeStyle];
                        const imageUrl = generatedEntry?.image_url || (item as unknown as ImageOption).image_url || null;
                        return (
                          <ImageCard
                            key={item.name}
                            slotType="interaction_item"
                            slotId={item.name}
                            imageUrl={imageUrl}
                            title={item.name}
                            isSmall
                          />
                        );
                      })}
                    </div>
                  </div>
                )}

                <div className="border-t border-gray-100 pt-4">
                  <button
                    onClick={applyImageStyle}
                    disabled={applyingStyle}
                    className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white text-sm font-medium px-5 py-2.5 rounded-xl"
                  >
                    {applyingStyle ? <Loader2 size={14} className="animate-spin" /> : <CheckCircle size={14} />}
                    Aplicar — {STYLE_LABELS[activeStyle]}
                  </button>
                  <p className="text-xs text-gray-400 mt-2">
                    Aplica o estilo selecionado a todas as imagens e atualiza a visualização do aluno.
                  </p>
                </div>
              </>
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
            ) : interactionOptions.map((io, idx) => (
              <div key={idx} className="border border-gray-200 rounded-lg p-4 mb-3">
                <p className="font-medium text-sm text-gray-800 mb-2">{io.instructions}</p>
                <p className="text-xs text-gray-500 mb-1">Tipo: {io.type}</p>
                <div className="flex flex-wrap gap-2 mb-2">
                  {io.items?.map((item, j) => (
                    <span key={j} className="bg-blue-100 text-blue-700 text-xs rounded-full px-2 py-0.5">{label(item)}</span>
                  ))}
                </div>
                <p className="text-xs text-gray-500">Zonas: {io.zones?.map(label).join(", ")}</p>
              </div>
            ))}
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
                  <span className="ml-1 text-purple-500">(perfil: {data.profile.name})</span>
                )}
              </label>
              <div className="relative">
                <select
                  value={assignStudentId}
                  onChange={(e) => setAssignStudentId(e.target.value)}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm appearance-none pr-8"
                >
                  <option value="">Sem aluno (por perfil)</option>
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
