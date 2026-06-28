"use client";
import { useEffect, useRef, useState } from "react";
import type { DragEvent } from "react";
import { useParams, useRouter } from "next/navigation";
import StudentLayout from "@/components/layout/StudentLayout";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { CheckCircle, Volume2, RotateCcw, FileDown, Loader2 } from "lucide-react";
import clsx from "clsx";

// â”€â”€â”€ Types â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
type ActivityItem = string | { name?: string; description?: string; image_url?: string; image_prompt?: string; emoji?: string; symbol?: string };
type ActivityZone = string | { name?: string; description?: string };
type InteractionType = "drag_and_drop" | "sequencing" | "multiple_choice";

const getLabel = (v: ActivityItem | ActivityZone): string => {
  if (typeof v === "string") return v;
  // Support both new schema ({ name }) and legacy OpenAI schema ({ description })
  return v.name || (v as Record<string, string>).description || JSON.stringify(v);
};

const getImageUrl = (v: ActivityItem): string | undefined =>
  typeof v === "string" ? undefined : v.image_url;

const getSymbol = (v: ActivityItem): string | undefined =>
  typeof v === "string" ? undefined : v.emoji || v.symbol;

interface InteractionOption {
  type: InteractionType;
  instructions: string;
  items: ActivityItem[];
  zones: ActivityZone[];
  correct_answer?: Record<string, string>;
  feedback_correct?: string;
  feedback_incorrect?: string;
}

interface ImageOption {
  id: string;
  description: string;
  is_active?: boolean;
  image_url?: string | null;
  emoji?: string;
  symbol?: string;
}

interface OutputData {
  text_adaptations?: Array<{ version: number; content: string }>;
  audio_options?: Array<{ id?: string; script: string; voice_style: string; audio_url?: string | null }>;
  interaction_options?: InteractionOption[];
  image_options?: ImageOption[];
}

// â”€â”€â”€ Item card (shared across interaction types) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function ItemCard({
  item,
  feedback,
  onClick,
  draggable = false,
  onDragStart,
  onDragEnd,
  isDragging = false,
  className,
}: {
  item: ActivityItem;
  feedback?: "correct" | "incorrect";
  onClick?: () => void;
  draggable?: boolean;
  onDragStart?: (event: DragEvent<HTMLDivElement>) => void;
  onDragEnd?: () => void;
  isDragging?: boolean;
  className?: string;
}) {
  const lbl = getLabel(item);
  const img = getImageUrl(item);
  const symbol = getSymbol(item);
  return (
    <div
      onClick={(event) => {
        if (!onClick) return;
        event.stopPropagation();
        onClick();
      }}
      draggable={draggable}
      onDragStart={onDragStart}
      onDragEnd={onDragEnd}
      className={clsx(
        "rounded-xl border-2 text-center select-none transition-all duration-200",
        draggable ? "cursor-grab active:cursor-grabbing active:scale-95" : "",
        onClick ? "cursor-pointer active:scale-95" : "",
        isDragging && "opacity-50 scale-95",
        feedback === "correct" && "border-green-400 bg-green-50 animate-pulse",
        feedback === "incorrect" && "border-red-400 bg-red-50",
        !feedback && "border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50",
        className,
      )}
    >
      {img && (
        <img src={img} alt={lbl} className="w-full h-24 object-cover rounded-t-xl" />
      )}
      {!img && symbol && (
        <div className="w-full h-24 rounded-t-xl bg-amber-50 flex items-center justify-center text-5xl">
          {symbol}
        </div>
      )}
      <p className={clsx("font-medium text-gray-800 px-2 py-2 text-sm", (img || symbol) && "border-t border-gray-100")}>
        {lbl}
      </p>
    </div>
  );
}

// â”€â”€â”€ DragAndDrop â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function DragAndDrop({
  interaction,
  answers,
  feedback,
  onAnswer,
}: {
  interaction: InteractionOption;
  answers: Record<string, string>;
  feedback: Record<string, "correct" | "incorrect">;
  onAnswer: (itemLabel: string, zoneLabel: string | null) => void;
}) {
  const [draggedLabel, setDraggedLabel] = useState<string | null>(null);
  const [overZone, setOverZone] = useState<string | null>(null);
  const [selectedLabel, setSelectedLabel] = useState<string | null>(null);
  const isLocked = Object.keys(feedback).length > 0;

  function handleDragStart(event: DragEvent<HTMLDivElement>, itemLabel: string) {
    if (isLocked) return;
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", itemLabel);
    setDraggedLabel(itemLabel);
  }

  function finishDrag() {
    setDraggedLabel(null);
    setOverZone(null);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>, zoneLabel: string) {
    event.preventDefault();
    const itemLabel = event.dataTransfer.getData("text/plain") || draggedLabel;
    if (itemLabel && !isLocked) {
      onAnswer(itemLabel, zoneLabel);
    }
    setSelectedLabel(null);
    finishDrag();
  }

  function handlePoolDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    const itemLabel = event.dataTransfer.getData("text/plain") || draggedLabel;
    if (itemLabel && !isLocked) {
      onAnswer(itemLabel, null);
    }
    setSelectedLabel(null);
    finishDrag();
  }

  function handleZoneClick(zoneLabel: string) {
    if (selectedLabel && !isLocked) {
      onAnswer(selectedLabel, zoneLabel);
      setSelectedLabel(null);
    }
  }

  const unplaced = interaction.items.filter((item) => !answers[getLabel(item)]);

  return (
    <>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-5">
        {interaction.zones.map((zone) => {
          const zoneLabel = getLabel(zone);
          const placed = interaction.items.filter((item) => answers[getLabel(item)] === zoneLabel);
          return (
            <div
              key={zoneLabel}
              onDragOver={(event) => {
                event.preventDefault();
                event.dataTransfer.dropEffect = "move";
                setOverZone(zoneLabel);
              }}
              onDragLeave={() => setOverZone((current) => current === zoneLabel ? null : current)}
              onDrop={(event) => handleDrop(event, zoneLabel)}
              onClick={() => handleZoneClick(zoneLabel)}
              className={clsx(
                "border-2 border-dashed rounded-xl p-3 min-h-44 bg-blue-50/30 transition-colors",
                overZone === zoneLabel ? "border-blue-500 bg-blue-100/70" : "border-blue-200"
              )}
            >
              <p className="text-center font-semibold text-blue-700 mb-3 text-base">{zoneLabel}</p>
              <div className="grid grid-cols-2 gap-2">
                {placed.map((item) => {
                  const itemLabel = getLabel(item);
                  return (
                    <ItemCard
                      key={itemLabel}
                      item={item}
                      feedback={feedback[itemLabel]}
                      draggable={!isLocked}
                      onDragStart={(event) => handleDragStart(event, itemLabel)}
                      onDragEnd={finishDrag}
                      onClick={() => setSelectedLabel((current) => current === itemLabel ? null : itemLabel)}
                      isDragging={draggedLabel === itemLabel}
                      className={clsx("text-xs min-h-28", selectedLabel === itemLabel && "ring-2 ring-blue-400 border-blue-400")}
                    />
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>

      <div
        onDragOver={(event) => {
          event.preventDefault();
          event.dataTransfer.dropEffect = "move";
        }}
        onDrop={handlePoolDrop}
        onClick={() => {
          if (selectedLabel && !isLocked) {
            onAnswer(selectedLabel, null);
            setSelectedLabel(null);
          }
        }}
        className="rounded-xl border border-gray-100 bg-gray-50 p-3 mb-4"
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {unplaced.map((item) => {
            const itemLabel = getLabel(item);
            return (
              <ItemCard
                key={itemLabel}
                item={item}
                draggable={!isLocked}
                onDragStart={(event) => handleDragStart(event, itemLabel)}
                onDragEnd={finishDrag}
                onClick={() => setSelectedLabel((current) => current === itemLabel ? null : itemLabel)}
                isDragging={draggedLabel === itemLabel}
                className={clsx("min-h-32", selectedLabel === itemLabel && "ring-2 ring-blue-400 border-blue-400")}
              />
            );
          })}
        </div>
      </div>
    </>
  );
}

function Sequencing({
  interaction,
  answers,
  feedback,
  onAnswer,
}: {
  interaction: InteractionOption;
  answers: Record<string, string>;
  feedback: Record<string, "correct" | "incorrect">;
  onAnswer: (itemLabel: string, zoneLabel: string | null) => void;
}) {
  const zones = interaction.zones;

  // Items already ordered, sorted by their zone index
  const ordered = interaction.items
    .filter((item) => answers[getLabel(item)])
    .sort((a, b) => {
      const ia = zones.findIndex((z) => getLabel(z) === answers[getLabel(a)]);
      const ib = zones.findIndex((z) => getLabel(z) === answers[getLabel(b)]);
      return ia - ib;
    });

  const unplaced = interaction.items.filter((item) => !answers[getLabel(item)]);

  const handleTap = (item: ActivityItem) => {
    const nextZone = zones[ordered.length];
    if (nextZone) onAnswer(getLabel(item), getLabel(nextZone));
  };

  const handleReset = () => {
    interaction.items.forEach((item) => onAnswer(getLabel(item), null));
  };

  return (
    <>
      {/* Sequence built so far */}
      {ordered.length > 0 && (
        <div className="space-y-2 mb-4">
          {ordered.map((item, idx) => {
            const lbl = getLabel(item);
            const fb = feedback[lbl];
            return (
              <div
                key={lbl}
                className={clsx(
                  "flex items-center gap-3 rounded-xl border-2 px-4 py-3",
                  fb === "correct" && "border-green-400 bg-green-50",
                  fb === "incorrect" && "border-red-400 bg-red-50",
                  !fb && "border-blue-200 bg-white",
                )}
              >
                <span className="text-lg font-bold text-blue-600 w-7 text-center">{idx + 1}Â°</span>
                <span className="font-medium text-gray-800">{lbl}</span>
                {fb === "correct" && <span className="ml-auto text-green-600 text-sm font-bold">âœ“</span>}
                {fb === "incorrect" && <span className="ml-auto text-red-500 text-sm font-bold">âœ—</span>}
              </div>
            );
          })}
        </div>
      )}

      {/* Items still to place */}
      {unplaced.length > 0 && (
        <>
          <p className="text-center text-sm text-gray-500 mb-3">
            Toque no item que vem em <strong>{ordered.length + 1}Â° lugar</strong>
          </p>
          <div className="flex flex-wrap gap-2 justify-center mb-4">
            {unplaced.map((item) => (
              <ItemCard
                key={getLabel(item)}
                item={item}
                onClick={() => handleTap(item)}
                className="w-32"
              />
            ))}
          </div>
        </>
      )}

      {/* Reset */}
      {ordered.length > 0 && !Object.keys(feedback).length && (
        <button
          onClick={handleReset}
          className="w-full flex items-center justify-center gap-2 border border-gray-200 text-gray-500 text-sm py-2 rounded-xl mt-1 hover:bg-gray-50"
        >
          <RotateCcw size={13} /> RecomeÃ§ar
        </button>
      )}
    </>
  );
}

// â”€â”€â”€ MultipleChoice â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
function MultipleChoice({
  interaction,
  answers,
  feedback,
  onAnswer,
}: {
  interaction: InteractionOption;
  answers: Record<string, string>;
  feedback: Record<string, "correct" | "incorrect">;
  onAnswer: (itemLabel: string, zoneLabel: string | null) => void;
}) {
  const itemLabel = getLabel(interaction.items[0] ?? "Minha resposta");
  const selected = answers[itemLabel];

  return (
    <div className="grid grid-cols-1 gap-3 mb-4">
      {interaction.zones.map((zone) => {
        const zoneLabel = getLabel(zone);
        const isSelected = selected === zoneLabel;
        const fb = isSelected ? feedback[itemLabel] : undefined;
        return (
          <button
            key={zoneLabel}
            onClick={() => onAnswer(itemLabel, isSelected ? null : zoneLabel)}
            className={clsx(
              "w-full rounded-xl border-2 px-5 py-4 text-left font-medium text-base transition-all duration-200 active:scale-98",
              isSelected && fb === "correct" && "border-green-400 bg-green-50 text-green-800",
              isSelected && fb === "incorrect" && "border-red-400 bg-red-50 text-red-800",
              isSelected && !fb && "border-blue-400 bg-blue-50 text-blue-800",
              !isSelected && "border-gray-200 bg-white text-gray-700 hover:border-blue-300 hover:bg-blue-50",
            )}
          >
            {zoneLabel}
          </button>
        );
      })}
    </div>
  );
}

// â”€â”€â”€ Main page â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
export default function StudentActivityPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [title, setTitle] = useState<string | null>(null);
  const [output, setOutput] = useState<OutputData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Record<string, "correct" | "incorrect">>({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<{ score: number; max_score: number; percentage: number } | null>(null);
  const [startTime] = useState<number>(Date.now());
  const [exporting, setExporting] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  async function handleExportPDF() {
    setExporting(true);
    try {
      const response = await api.get(`/student/activities/${id}/pdf`, {
        responseType: "blob",
      });
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${title ?? "atividade"}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch {
      toast.error("Não foi possível exportar o PDF.");
    } finally {
      setExporting(false);
    }
  }

  useEffect(() => {
    api.get(`/student/activities/${id}`)
      .then(async (r) => {
        setTitle(r.data.title ?? null);
        setOutput(r.data.output);
        await api.post(`/student/activities/${id}/start`).catch(() => {});
      })
      .catch(() => {
        toast.error("Atividade nÃ£o encontrada.");
        router.push("/student");
      });
  }, [id]);

  function handleAnswer(itemLabel: string, zoneLabel: string | null) {
    setAnswers((prev) => {
      const next = { ...prev };
      if (zoneLabel === null) {
        delete next[itemLabel];
      } else {
        next[itemLabel] = zoneLabel;
      }
      return next;
    });
  }

  async function handleSubmit() {
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    try {
      const { data } = await api.post(`/student/activities/${id}/submit`, {
        response: answers,
        completion_time_seconds: elapsed,
      });
      setResult(data);
      setSubmitted(true);

      // Build per-item feedback from correct_answer
      const interaction = output?.interaction_options?.[0];
      const correctAnswer = interaction?.correct_answer ?? {};
      const interactionType = interaction?.type;
      const newFeedback: Record<string, "correct" | "incorrect"> = {};

      if (interactionType === "multiple_choice") {
        const itemLabel = getLabel(interaction?.items?.[0] ?? "Minha resposta");
        const chosen = answers[itemLabel];
        newFeedback[itemLabel] = chosen === correctAnswer.correct_zone ? "correct" : "incorrect";
      } else {
        for (const [itemLabel, chosenZone] of Object.entries(answers)) {
          newFeedback[itemLabel] = chosenZone === correctAnswer[itemLabel] ? "correct" : "incorrect";
        }
      }
      setFeedback(newFeedback);
    } catch {
      toast.error("Erro ao enviar resposta.");
    }
  }

  const exportButton = output ? (
    <button
      onClick={handleExportPDF}
      disabled={exporting}
      aria-label="Exportar atividade em PDF para impressão"
      className="inline-flex items-center gap-1.5 text-sm font-medium text-blue-700 border border-blue-200 bg-white hover:bg-blue-50 px-3 py-1.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    >
      {exporting ? (
        <Loader2 size={15} className="animate-spin" />
      ) : (
        <FileDown size={15} />
      )}
      {exporting ? "Gerando…" : "Exportar PDF"}
    </button>
  ) : null;

  if (!output) return (
    <StudentLayout>
      <div className="flex justify-center py-20">
        <div className="animate-spin h-10 w-10 border-4 border-blue-600 border-t-transparent rounded-full" />
      </div>
    </StudentLayout>
  );

  const text = output.text_adaptations?.[0]?.content;
  const audio = output.audio_options?.[0];
  const interaction = output.interaction_options?.[0];
  const visualImages = (output.image_options ?? []).filter((img) => img.is_active && (img.image_url || img.emoji || img.symbol));

  const allAnswered = interaction
    ? interaction.items.every((item) => answers[getLabel(item)])
    : false;

  return (
    <StudentLayout headerAction={exportButton}>
      {title && (
        <h1 className="text-lg font-bold text-gray-900 mb-4">{title}</h1>
      )}

      {submitted && result ? (
        <div className="text-center py-10">
          <CheckCircle size={48} className="mx-auto text-green-500 mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">ParabÃ©ns!</h2>
          <p className="text-gray-600 mb-4">VocÃª completou a atividade.</p>
          <div className="inline-block bg-green-50 border border-green-200 rounded-2xl px-8 py-4 mb-6">
            <p className="text-4xl font-bold text-green-700">{result.percentage}%</p>
            <p className="text-sm text-gray-500">{result.score} de {result.max_score} pontos</p>
          </div>

          {/* Per-item feedback */}
          {interaction && Object.keys(feedback).length > 0 && (
            <div className="text-left max-w-sm mx-auto mb-6 space-y-2">
              {interaction.items.map((item) => {
                const lbl = getLabel(item);
                const fb = feedback[lbl];
                const correct = interaction.correct_answer?.[lbl] ?? interaction.correct_answer?.correct_zone;
                return (
                  <div key={lbl} className={clsx("flex items-center justify-between rounded-lg px-4 py-2 text-sm", fb === "correct" ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700")}>
                    <span className="font-medium">{lbl}</span>
                    <span className="text-xs">{fb === "correct" ? "âœ“ correto" : correct ? `âœ— era "${correct}"` : "âœ— incorreto"}</span>
                  </div>
                );
              })}
            </div>
          )}

          <button onClick={() => router.push("/student")}
            className="block mx-auto bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2.5 rounded-xl">
            Voltar
          </button>
        </div>
      ) : (
        <div>
          {visualImages.length > 0 && (
            <div className="flex gap-3 overflow-x-auto mb-4 pb-1">
              {visualImages.map((img) => (
                <div key={img.id} className="flex-shrink-0 text-center">
                  {img.image_url ? (
                    <img
                      src={img.image_url}
                      alt={img.description}
                      className="w-36 h-36 object-cover rounded-xl border border-blue-100 shadow-sm"
                    />
                  ) : (
                    <div className="w-36 h-36 rounded-xl border border-blue-100 shadow-sm bg-amber-50 flex items-center justify-center text-6xl">
                      {img.emoji || img.symbol}
                    </div>
                  )}
                  <p className="text-xs text-gray-500 mt-1">{img.description}</p>
                </div>
              ))}
            </div>
          )}

          {text && (
            <div className="bg-white rounded-2xl border border-blue-100 p-6 mb-4">
              <pre className="text-base text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">{text}</pre>
            </div>
          )}

          {audio && (
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-4 flex items-start gap-3">
              <Volume2 size={18} className="text-blue-500 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-xs text-blue-500 font-medium mb-1">Ãudio â€” {audio.voice_style}</p>
                {audio.audio_url && (
                  <div className="space-y-2 mb-3">
                    <button
                      type="button"
                      onClick={() => {
                        audioRef.current?.play().catch(() => toast.error("Não foi possível iniciar o áudio."));
                      }}
                      className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-xl"
                    >
                      <Volume2 size={16} /> Ouvir narração
                    </button>
                    {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
                    <audio ref={audioRef} controls src={audio.audio_url} className="w-full h-9 rounded-lg" />
                  </div>
                )}
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{audio.script}</pre>
              </div>
            </div>
          )}

          {interaction && (
            <div className="bg-white rounded-2xl border border-blue-100 p-6">
              {interaction.instructions && (
                <p className="font-bold text-gray-900 text-center mb-5 text-lg">{interaction.instructions}</p>
              )}

              {interaction.type === "drag_and_drop" && (
                <DragAndDrop interaction={interaction} answers={answers} feedback={feedback} onAnswer={handleAnswer} />
              )}
              {interaction.type === "sequencing" && (
                <Sequencing interaction={interaction} answers={answers} feedback={feedback} onAnswer={handleAnswer} />
              )}
              {interaction.type === "multiple_choice" && (
                <MultipleChoice interaction={interaction} answers={answers} feedback={feedback} onAnswer={handleAnswer} />
              )}

              {allAnswered && !submitted && (
                <button
                  onClick={handleSubmit}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-xl text-lg mt-2"
                >
                  Enviar resposta!
                </button>
              )}

              {Object.keys(answers).length > 0 && !allAnswered && !submitted && interaction.type !== "sequencing" && (
                <button
                  onClick={() => setAnswers({})}
                  className="w-full flex items-center justify-center gap-2 border border-gray-200 text-gray-500 text-sm py-2 rounded-xl mt-2 hover:bg-gray-50"
                >
                  <RotateCcw size={13} /> RecomeÃ§ar
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </StudentLayout>
  );
}
