"use client";
import { useEffect, useRef, useState } from "react";
import type { DragEvent } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import StudentLayout from "@/components/layout/StudentLayout";
import StudentHeaderMenu from "@/components/layout/StudentHeaderMenu";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { ArrowLeft, ArrowRight, CheckCircle, FileDown, Loader2, RotateCcw, Volume2, BookOpen } from "lucide-react";
import clsx from "clsx";
import { getDisciplineHref, groupActivitiesByDiscipline, type StudentActivityCard } from "@/lib/student-area";

// Types
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
  audio_options?: Array<{ id?: string; script: string; tts_script?: string; voice_style: string; audio_url?: string | null; rhythm?: number }>;
  interaction_options?: InteractionOption[];
  image_options?: ImageOption[];
}
interface StoryData {
  id: string;
  title: string;
  content: string;
  audio_options?: Array<{ id?: string; script: string; tts_script?: string; voice_style?: string; audio_url?: string | null; rhythm?: number }>;
  image_options?: ImageOption[];
}

// Types
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
// Drag and drop
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
                <span className="text-lg font-bold text-blue-600 w-7 text-center">{idx + 1}º</span>
                <span className="font-medium text-gray-800">{lbl}</span>
                {fb === "correct" && <span className="ml-auto text-green-600 text-sm font-bold">Correto</span>}
                {fb === "incorrect" && <span className="ml-auto text-red-500 text-sm font-bold">Rever</span>}
              </div>
            );
          })}
        </div>
      )}

      {/* Items still to place */}
      {unplaced.length > 0 && (
        <>
          <p className="text-center text-sm text-gray-500 mb-3">
            Toque no item que vem em <strong>{ordered.length + 1}º lugar</strong>
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

// Multiple choice
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

// Main page
export default function StudentActivityPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [title, setTitle] = useState<string | null>(null);
  const [story, setStory] = useState<StoryData | null>(null);
  const [discipline, setDiscipline] = useState<string | null>(null);
  const [activities, setActivities] = useState<StudentActivityCard[]>([]);
  const [output, setOutput] = useState<OutputData | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [feedback, setFeedback] = useState<Record<string, "correct" | "incorrect">>({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<{ score: number; max_score: number; percentage: number } | null>(null);
  const [startTime] = useState<number>(Date.now());
  const [exporting, setExporting] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const storyAudioRef = useRef<HTMLAudioElement | null>(null);

  function playNarration(
    option: { script?: string; tts_script?: string; audio_url?: string | null; rhythm?: number },
    audioElement: HTMLAudioElement | null,
  ) {
    if (option.audio_url && audioElement) {
      audioElement.play().catch(() => toast.error("Não foi possível iniciar o áudio."));
      return;
    }

    const textToSpeak = (option.tts_script || option.script || "").trim();
    if (!textToSpeak) {
      toast.error("Não há roteiro de áudio para reproduzir.");
      return;
    }
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      toast.error("Este navegador não suporta leitura em voz alta.");
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = "pt-BR";
    utterance.rate = Math.max(0.5, Math.min(1.2, option.rhythm ?? 0.9));
    window.speechSynthesis.speak(utterance);
  }

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
    Promise.all([
      api.get(`/student/activities/${id}`),
      api.get("/student/activities"),
    ])
      .then(async ([activityRes, listRes]) => {
        setTitle(activityRes.data.title ?? null);
        setDiscipline(activityRes.data.discipline ?? null);
        setStory(activityRes.data.story ?? null);
        setOutput(activityRes.data.output);
        setActivities(listRes.data ?? []);
        await api.post(`/student/activities/${id}/start`).catch(() => {});
      })
      .catch(() => {
        toast.error("Atividade não encontrada.");
        router.push("/student");
      });
  }, [id, router]);

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
  const storyImages = (story?.image_options ?? []).filter((img) => img.is_active && (img.image_url || img.emoji || img.symbol));
  const storyAudio = story?.audio_options?.[0];

  const allAnswered = interaction
    ? interaction.items.every((item) => answers[getLabel(item)])
    : false;

  const disciplineGroups = groupActivitiesByDiscipline(activities);
  const nextActivityId = (() => {
    const ordered = [...activities].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
    const current = ordered.findIndex((activity) => activity.id === id);
    if (current === -1) return null;

    if (discipline) {
      const sameDiscipline = ordered.filter((activity) => (activity.discipline || "Sem disciplina") === discipline);
      const currentInDiscipline = sameDiscipline.findIndex((activity) => activity.id === id);
      if (currentInDiscipline >= 0 && sameDiscipline[currentInDiscipline + 1]) {
        return sameDiscipline[currentInDiscipline + 1].id;
      }
    }

    return ordered[current + 1]?.id ?? null;
  })();

  const headerAction = (
    <StudentHeaderMenu
      disciplines={disciplineGroups.map((group) => ({
        id: group.id,
        label: group.label,
        href: getDisciplineHref(group.id),
      }))}
      onExportAll={handleExportPDF}
      exportDisabled={exporting}
    />
  );

  return (
    <StudentLayout headerAction={headerAction}>
      {story && (
        <section className="bg-white rounded-2xl border border-amber-100 shadow-sm overflow-hidden mb-5">
          <div className="bg-amber-50 border-b border-amber-100 px-5 py-4">
            <div className="flex items-center gap-2 min-w-0">
              <BookOpen size={20} className="text-amber-600 flex-shrink-0" />
              <h2 className="font-bold text-gray-900">{story.title}</h2>
            </div>
          </div>
          <div className="p-5">
            {storyImages.length > 0 && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                {storyImages.map((img) => (
                  <div key={img.id} className="rounded-xl border border-amber-100 bg-amber-50 text-center overflow-hidden">
                    {img.image_url ? (
                      <img src={img.image_url} alt={img.description} className="w-full h-28 object-cover" />
                    ) : (
                      <div className="h-28 flex items-center justify-center text-5xl">{img.emoji || img.symbol}</div>
                    )}
                    <p className="text-xs text-gray-600 px-2 py-2">{img.description}</p>
                  </div>
                ))}
              </div>
            )}

            <div className="rounded-2xl border border-blue-100 bg-blue-50/30 p-4 mb-4">
              <pre className="text-base text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">{story.content}</pre>
            </div>

            {storyAudio && (
              <div className="rounded-xl border border-blue-100 bg-white p-4">
                <div className="flex items-center gap-2 text-blue-600 text-sm font-semibold mb-2">
                  <Volume2 size={16} /> Narração do conto
                </div>
                <div className="space-y-2 mb-3">
                  <button
                    type="button"
                    onClick={() => playNarration(storyAudio, storyAudioRef.current)}
                    className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-xl"
                  >
                    <Volume2 size={16} /> Ouvir narração
                  </button>
                  {storyAudio.audio_url && (
                    // eslint-disable-next-line jsx-a11y/media-has-caption
                    <audio ref={storyAudioRef} controls src={storyAudio.audio_url} className="w-full h-9 rounded-lg" />
                  )}
                </div>
                {!storyAudio.audio_url && (
                  <p className="text-xs text-blue-500 mb-3">
                    Áudio MP3 ainda não gerado. Usando leitura em voz alta do navegador.
                  </p>
                )}
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{storyAudio.script}</pre>
              </div>
            )}
          </div>
        </section>
      )}

      {title && (
        <h1 className="text-lg font-bold text-gray-900 mb-4">{title}</h1>
      )}

      <div
        className={clsx(
          "transition duration-300",
          submitted && result && "pointer-events-none select-none opacity-60 blur-[3px]",
        )}
      >
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
                <p className="text-xs text-blue-500 font-medium mb-1">Narração — {audio.voice_style}</p>
                <div className="space-y-2 mb-3">
                  <button
                    type="button"
                    onClick={() => playNarration(audio, audioRef.current)}
                    className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-xl"
                  >
                    <Volume2 size={16} /> Ouvir narração
                  </button>
                  {audio.audio_url && (
                    <audio ref={audioRef} controls src={audio.audio_url} className="w-full h-9 rounded-lg" />
                  )}
                </div>
                {!audio.audio_url && (
                  <p className="text-xs text-blue-500 mb-3">
                    Áudio MP3 ainda não gerado. Usando leitura em voz alta do navegador.
                  </p>
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
                  <RotateCcw size={13} /> Recomeçar
                </button>
              )}
            </div>
          )}
      </div>

      {submitted && result && (
        <>
          <Link
            href="/student"
            className="fixed left-0 top-1/2 z-40 flex -translate-y-1/2 items-center gap-2 rounded-r-2xl border border-l-0 border-white/70 bg-white/90 px-3 py-4 text-sm font-semibold text-blue-700 shadow-xl backdrop-blur"
          >
            <ArrowLeft size={18} />
            Lista
          </Link>

          <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-950/35 px-4 py-6 backdrop-blur-sm [animation:result-backdrop-in_180ms_ease-out]">
            <section
              role="dialog"
              aria-modal="true"
              aria-labelledby="activity-result-title"
              className="w-full max-w-xl overflow-hidden rounded-3xl border border-white/70 bg-white shadow-2xl [animation:result-modal-in_220ms_ease-out]"
            >
              <div className="border-b border-slate-100 bg-gradient-to-br from-emerald-50 to-blue-50 px-6 py-6 text-center">
                <CheckCircle size={44} className="mx-auto mb-3 text-emerald-500" />
                <h2 id="activity-result-title" className="text-2xl font-bold text-slate-950">
                  Parabéns!
                </h2>
                <p className="mt-1 text-sm text-slate-600">Você completou a atividade.</p>
                <div className="mt-5 inline-flex items-end gap-2 rounded-2xl border border-emerald-100 bg-white px-6 py-4 shadow-sm">
                  <span className="text-5xl font-black leading-none text-emerald-600">{result.percentage}%</span>
                  <span className="pb-1 text-sm font-medium text-slate-500">
                    {result.score} de {result.max_score} pontos
                  </span>
                </div>
              </div>

              {interaction && Object.keys(feedback).length > 0 && (
                <div className="max-h-64 overflow-auto px-6 py-4">
                  <p className="mb-3 text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">
                    Resultado individual
                  </p>
                  <div className="space-y-2">
                    {interaction.items.map((item) => {
                      const itemLabel = getLabel(item);
                      const displayLabel =
                        interaction.type === "multiple_choice"
                          ? answers[itemLabel] || itemLabel
                          : itemLabel;
                      const itemFeedback = feedback[itemLabel];
                      const correct = interaction.correct_answer?.[itemLabel] ?? interaction.correct_answer?.correct_zone;

                      return (
                        <div
                          key={itemLabel}
                          className={clsx(
                            "flex items-center justify-between gap-3 rounded-2xl border px-4 py-3 text-sm",
                            itemFeedback === "correct"
                              ? "border-emerald-100 bg-emerald-50 text-emerald-800"
                              : "border-rose-100 bg-rose-50 text-rose-800",
                          )}
                        >
                          <span className="min-w-0 truncate font-semibold">{displayLabel}</span>
                          <span className="shrink-0 text-xs font-bold">
                            {itemFeedback === "correct" ? "Correto" : correct ? `Resposta: ${correct}` : "Rever"}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="flex flex-col gap-3 border-t border-slate-100 bg-white px-6 py-5 sm:flex-row">
                {nextActivityId ? (
                  <Link
                    href={`/student/activities/${nextActivityId}`}
                    className="inline-flex flex-1 items-center justify-center gap-2 rounded-2xl bg-blue-600 px-6 py-3 text-base font-bold text-white transition-colors hover:bg-blue-700"
                  >
                    Próxima atividade
                    <ArrowRight size={18} />
                  </Link>
                ) : (
                  <Link
                    href="/student"
                    className="inline-flex flex-1 items-center justify-center gap-2 rounded-2xl bg-blue-600 px-6 py-3 text-base font-bold text-white transition-colors hover:bg-blue-700"
                  >
                    Voltar para lista
                  </Link>
                )}
                <Link
                  href="/student"
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-blue-200 bg-white px-6 py-3 text-base font-semibold text-blue-700 transition-colors hover:bg-blue-50"
                >
                  <ArrowLeft size={18} />
                  Lista
                </Link>
              </div>
            </section>
          </div>
        </>
      )}
    </StudentLayout>
  );
}
