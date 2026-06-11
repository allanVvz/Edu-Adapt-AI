"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import StudentLayout from "@/components/layout/StudentLayout";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { CheckCircle, Volume2 } from "lucide-react";

interface OutputData {
  text_adaptations?: Array<{ version: number; content: string }>;
  audio_options?: Array<{ id: string; script: string; voice_style: string }>;
  interaction_options?: Array<{
    type: string;
    instructions: string;
    items: string[];
    zones: string[];
    feedback_correct: string;
    feedback_incorrect: string;
  }>;
}

export default function StudentActivityPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [output, setOutput] = useState<OutputData | null>(null);
  const [attemptId, setAttemptId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState<{ score: number; max_score: number; percentage: number } | null>(null);
  const [startTime, setStartTime] = useState<number>(Date.now());

  useEffect(() => {
    api.get(`/student/activities/${id}`)
      .then(async (r) => {
        setOutput(r.data.output);
        const { data: start } = await api.post(`/student/activities/${id}/start`);
        setAttemptId(start.attempt_id);
        setStartTime(Date.now());
      })
      .catch(() => {
        toast.error("Atividade não encontrada.");
        router.push("/student");
      });
  }, [id]);

  async function handleSubmit() {
    const elapsed = Math.round((Date.now() - startTime) / 1000);
    try {
      const { data } = await api.post(`/student/activities/${id}/submit`, {
        response: answers,
        completion_time_seconds: elapsed,
      });
      setResult(data);
      setSubmitted(true);
    } catch {
      toast.error("Erro ao enviar resposta.");
    }
  }

  function setAnswer(item: string, zone: string) {
    setAnswers((prev) => ({ ...prev, [item]: zone }));
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

  return (
    <StudentLayout>
      {submitted && result ? (
        <div className="text-center py-10">
          <CheckCircle size={48} className="mx-auto text-green-500 mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Parabéns!</h2>
          <p className="text-gray-600 mb-4">Você completou a atividade.</p>
          <div className="inline-block bg-green-50 border border-green-200 rounded-2xl px-8 py-4 mb-6">
            <p className="text-4xl font-bold text-green-700">{result.percentage}%</p>
            <p className="text-sm text-gray-500">{result.score} de {result.max_score} pontos</p>
          </div>
          <button onClick={() => router.push("/student")}
            className="block mx-auto bg-blue-600 hover:bg-blue-700 text-white font-medium px-6 py-2.5 rounded-xl">
            Voltar
          </button>
        </div>
      ) : (
        <div>
          {text && (
            <div className="bg-white rounded-2xl border border-blue-100 p-6 mb-4">
              <pre className="text-base text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">{text}</pre>
            </div>
          )}

          {audio && (
            <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 mb-4 flex items-start gap-3">
              <Volume2 size={18} className="text-blue-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-xs text-blue-500 font-medium mb-1">Áudio disponível — {audio.voice_style}</p>
                <pre className="text-sm text-gray-700 whitespace-pre-wrap font-sans">{audio.script}</pre>
              </div>
            </div>
          )}

          {interaction && (
            <div className="bg-white rounded-2xl border border-blue-100 p-6">
              <p className="font-bold text-gray-900 text-center mb-4 text-lg">{interaction.instructions}</p>

              <div className="grid grid-cols-2 gap-4 mb-6">
                {interaction.zones.map((zone) => (
                  <div key={zone} className="border-2 border-dashed border-blue-200 rounded-xl p-3 min-h-28">
                    <p className="text-center font-semibold text-blue-600 mb-2 text-sm">{zone}</p>
                    <div className="space-y-1.5">
                      {interaction.items.filter((item) => answers[item] === zone).map((item) => (
                        <div key={item} className="bg-blue-100 text-blue-800 text-sm font-medium rounded-lg px-3 py-1.5 text-center">
                          {item}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex flex-wrap gap-2 justify-center mb-6">
                {interaction.items.filter((item) => !answers[item]).map((item) => (
                  <div key={item} className="relative">
                    <p className="text-xs text-center text-gray-400 mb-1">Mover para:</p>
                    <div className="flex gap-1">
                      {interaction.zones.map((zone) => (
                        <button
                          key={zone}
                          onClick={() => setAnswer(item, zone)}
                          className="bg-white border border-gray-300 hover:border-blue-400 hover:bg-blue-50 rounded-lg px-3 py-2 text-sm font-medium text-gray-700 transition-colors"
                        >
                          {item} → {zone}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {interaction.items.every((item) => answers[item]) && (
                <button
                  onClick={handleSubmit}
                  className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-3 rounded-xl text-lg"
                >
                  Enviar resposta!
                </button>
              )}

              {Object.keys(answers).length > 0 && !interaction.items.every((item) => answers[item]) && (
                <button
                  onClick={() => setAnswers({})}
                  className="w-full border border-gray-200 text-gray-500 text-sm py-2 rounded-xl mt-2"
                >
                  Recomeçar
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </StudentLayout>
  );
}
