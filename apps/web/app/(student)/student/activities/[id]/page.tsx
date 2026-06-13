"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import StudentLayout from "@/components/layout/StudentLayout";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { CheckCircle, Volume2, RotateCcw } from "lucide-react";
import clsx from "clsx";

// ─── Types ────────────────────────────────────────────────────────────────────
type ActivityItem = string | { name: string; image_url?: string; image_prompt?: string };
type ActivityZone = string | { name: string };
type InteractionType = "drag_and_drop" | "sequencing" | "multiple_choice";

const getLabel = (v: ActivityItem | ActivityZone): string => {
  if (typeof v === "string") return v;
  // Support both new schema ({ name }) and legacy OpenAI schema ({ description })
  return v.name || (v as Record<string, string>).description || JSON.stringify(v);
};

const getImageUrl = (v: ActivityItem): string | undefined =>
  typeof v === "string" ? undefined : v.image_url;

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
}

interface OutputData {
  text_adaptations?: Array<{ version: number; content: string }>;
  audio_options?: Array<{ id?: string; script: string; voice_style: string }>;
  interaction_options?: InteractionOption[];
  image_options?: ImageOption[];
}

// ─── Item card (shared across interaction types) ──────────────────────────────
function ItemCard({
  item,
  feedback,
  onClick,
  className,
}: {
  item: ActivityItem;
  feedback?: "correct" | "incorrect";
  onClick?: () => void;
  className?: string;
}) {
  const lbl = getLabel(item);
  const img = getImageUrl(item);
  return (
    <div
      onClick={onClick}
      className={clsx(
        "rounded-xl border-2 text-center select-none transition-all duration-200",
        onClick ? "cursor-pointer active:scale-95" : "",
        feedback === "correct" && "border-green-400 bg-green-50 animate-pulse",
        feedback === "incorrect" && "border-red-400 bg-red-50",
        !feedback && "border-gray-200 bg-white hover:border-blue-300 hover:bg-blue-50",
        className,
      )}
    >
      {img && (
        <img src={img} alt={lbl} className="w-full h-24 object-cover rounded-t-xl" />
      )}
      <p className={clsx("font-medium text-gray-800 px-2 py-2 text-sm", img && "border-t border-gray-100")}>
        {lbl}
      </p>
    </div>
  );
}

// ─── DragAndDrop ──────────────────────────────────────────────────────────────
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
  return (
    <>
      <div className="grid grid-cols-2 gap-3 mb-5">
        {interaction.zones.map((zone) => {
          const zoneLabel = getLabel(zone);
          const placed = interaction.items.filter((i) => answers[getLabel(i)] === zoneLabel);
          return (
            <div key={zoneLabel} className="border-2 border-dashed border-blue-200 rounded-xl p-3 min-h-28 bg-blue-50/30">
              <p className="text-center font-semibold text-blue-600 mb-2 text-sm">{zoneLabel}</p>
              <div className="space-y-2">
                {placed.map((item) => (
                  <ItemCard
                    key={getLabel(item)}
                    item={item}
                    feedback={feedback[getLabel(item)]}
                    onClick={() => onAnswer(getLabel(item), null)}
                    className="text-xs"
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex flex-wrap gap-2 justify-center mb-4">
        {interaction.items
          .filter((item) => !answers[getLabel(item)])
          .map((item) => {
            const itemLabel = getLabel(item);
            return (
              <div key={itemLabel} className="flex flex-col items-center gap-1.5">
                <ItemCard item={item} className="w-28" />
                <div className="flex gap-1 flex-wrap justify-center">
                  {interaction.zones.map((zone) => {
                    const zoneLabel = getLabel(zone);
                    return (
                      <button
                        key={zoneLabel}
                        onClick={() => onAnswer(itemLabel, zoneLabel)}
                        className="bg-white border border-gray-300 hover:border-blue-400 hover:bg-blue-50 rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-700 transition-colors"
                      >
                        → {zoneLabel}
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
      </div>
    </>
  );
}

// ─── Sequencing ───────────────────────────────────────────────────────────────
// Tap items in the correct order — each tap assigns the next position.
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
                <span className="text-lg font-bold text-blue-600 w-7 text-center">{idx + 1}°</span>
                <span className="font-medium text-gray-800">{lbl}</span>
                {fb === "correct" && <span className="ml-auto text-green-600 text-sm font-bold">✓</span>}
                {fb === "incorrect" && <span className="ml-auto text-red-500 text-sm font-bold">✗</span>}
              </div>
            );
          })}
        </div>
      )}

      {/* Items still to place */}
      {unplaced.length > 0 && (
        <>
          <p className="text-center text-sm text-gray-500 mb-3">
            Toque no item que vem em <strong>{ordered.length + 1}° lugar</strong>
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
          <RotateCcw size={13} /> Recomeçar
        </button>
      )}
    </>
  );
}

// ─── MultipleChoice ───────────────────────────────────────────────────────────
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

// ─── Main page ────────────────────────────────────────────────────────────────
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

  useEffect(() => {
    api.get(`/student/activities/${id}`)
      .then(async (r) => {
        setTitle(r.data.title ?? null);
        setOutput(r.data.output);
        await api.post(`/student/activities/${id}/start`).catch(() => {});
      })
      .catch(() => {
        toast.error("Atividade não encontrada.");
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
  const visualImages = (output.image_options ?? []).filter((img) => img.is_active && img.image_url);

  const allAnswered = interaction
    ? interaction.items.every((item) => answers[getLabel(item)])
    : false;

  return (
    <StudentLayout>
      {title && (
        <h1 className="text-lg font-bold text-gray-900 mb-4">{title}</h1>
      )}

      {submitted && result ? (
        <div className="text-center py-10">
          <CheckCircle size={48} className="mx-auto text-green-500 mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Parabéns!</h2>
          <p className="text-gray-600 mb-4">Você completou a atividade.</p>
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
                    <span className="text-xs">{fb === "correct" ? "✓ correto" : correct ? `✗ era "${correct}"` : "✗ incorreto"}</span>
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
                  <img
                    src={img.image_url!}
                    alt={img.description}
                    className="w-36 h-36 object-cover rounded-xl border border-blue-100 shadow-sm"
                  />
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
              <div>
                <p className="text-xs text-blue-500 font-medium mb-1">Áudio — {audio.voice_style}</p>
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
                  <RotateCcw size={13} /> Recomeçar
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </StudentLayout>
  );
}
