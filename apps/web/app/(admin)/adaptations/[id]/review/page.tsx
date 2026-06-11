"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import AdminLayout from "@/components/layout/AdminLayout";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { CheckCircle, XCircle, RefreshCw, Send } from "lucide-react";
import clsx from "clsx";

const TABS = ["Texto", "Visual", "Imagens", "Áudio", "Interação", "Impressão", "Validação"] as const;
type Tab = (typeof TABS)[number];

interface AdaptationData {
  id: string;
  activity: { id: string; title: string } | null;
  profile: { id: string; name: string } | null;
  generated_by: string;
  status: string;
  version: number;
  output: Record<string, unknown>;
  validator_feedback: string | null;
  teacher_feedback: string | null;
}

export default function ReviewPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<AdaptationData | null>(null);
  const [tab, setTab] = useState<Tab>("Texto");
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => { load(); }, [id]);

  async function load() {
    const { data: d } = await api.get(`/adaptations/${id}`);
    setData(d);
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
  const audioOptions = (output.audio_options as Array<{ id: string; script: string; voice_style: string }>) || [];
  const interactionOptions = (output.interaction_options as Array<{ type: string; instructions: string; items: string[]; zones: string[] }>) || [];
  const visualModality = output.visual_modality as { type: string; instructions: string; print_version: Record<string, unknown> } | undefined;
  const printVersion = (output.print_version as Record<string, unknown>) || visualModality?.print_version || {};
  const validation = output.validation as { clarity_score: number; accessibility_score: number; pedagogical_score: number; approved: boolean; notes: string } | undefined;

  return (
    <AdminLayout>
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            {data.activity?.title || "Adaptação"} — v{data.version}
          </h1>
          <div className="flex items-center gap-2 mt-1">
            {data.profile && <span className="text-xs bg-purple-100 text-purple-700 rounded-full px-2 py-0.5">{data.profile.name}</span>}
            <span className={clsx("text-xs rounded-full px-2 py-0.5 font-medium", {
              "bg-yellow-100 text-yellow-700": data.status === "review",
              "bg-green-100 text-green-700": data.status === "approved" || data.status === "published",
              "bg-red-100 text-red-700": data.status === "rejected",
              "bg-gray-100 text-gray-500": data.status === "draft",
            })}>
              {data.status}
            </span>
            <span className="text-xs text-gray-400">gerado por {data.generated_by}</span>
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

      <div className="flex gap-1 mb-6 overflow-x-auto pb-1">
        {TABS.map((t) => (
          <button key={t} onClick={() => setTab(t)}
            className={clsx("px-4 py-2 text-sm font-medium rounded-lg whitespace-nowrap transition-colors", {
              "bg-blue-600 text-white": tab === t,
              "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50": tab !== t,
            })}>
            {t}
          </button>
        ))}
      </div>

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
            ) : audioOptions.map((a) => (
              <div key={a.id} className="bg-gray-50 rounded-lg p-4 mb-3">
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
                  {i.items?.map((item) => (
                    <span key={item} className="bg-blue-100 text-blue-700 text-xs rounded-full px-2 py-0.5">{item}</span>
                  ))}
                </div>
                <p className="text-xs text-gray-500">Zonas: {i.zones?.join(", ")}</p>
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
                  ].map(({ label, score }) => (
                    <div key={label} className="bg-gray-50 rounded-lg p-3">
                      <p className="text-xs text-gray-500">{label}</p>
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
    </AdminLayout>
  );
}
