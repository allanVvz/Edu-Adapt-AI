"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import clsx from "clsx";
import StudentLayout from "@/components/layout/StudentLayout";
import StudentHeaderMenu from "@/components/layout/StudentHeaderMenu";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import { ArrowRight, BarChart3, Clock, Trophy } from "lucide-react";
import {
  getDisciplineHref,
  getDisciplineTheme,
  groupActivitiesByDiscipline,
  type StudentResultCard,
} from "@/lib/student-area";

export default function StudentResultsPage() {
  const router = useRouter();
  const [userName, setUserName] = useState("");
  const [results, setResults] = useState<StudentResultCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const user = getUser();
    if (!user) {
      router.replace("/login");
      return;
    }
    if (user.role !== "student") {
      router.replace("/dashboard");
      return;
    }
    setUserName(user.name);

    api
      .get("/student/results")
      .then((r) => setResults(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [router]);

  async function handleExportAllPDF() {
    if (exporting) return;
    setExporting(true);
    try {
      const res = await api.get("/student/activities/export-all-pdf", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data], { type: "application/pdf" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = "minhas_atividades.pdf";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch {
      alert("Não foi possível gerar o PDF. Tente novamente.");
    } finally {
      setExporting(false);
    }
  }

  const disciplineGroups = groupActivitiesByDiscipline(results);
  const totalScore = results.reduce((sum, item) => sum + (item.score ?? 0), 0);
  const totalMax = results.reduce((sum, item) => sum + (item.max_score ?? 0), 0);
  const overall = totalMax > 0 ? Math.round((totalScore / totalMax) * 100) : null;

  return (
    <StudentLayout
      headerAction={
        <StudentHeaderMenu
          disciplines={disciplineGroups.map((group) => ({
            id: group.id,
            label: group.label,
            href: getDisciplineHref(group.id),
          }))}
          onExportAll={handleExportAllPDF}
          exportDisabled={exporting || loading}
          resultsHref="/student/results"
        />
      }
    >
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-500">Resultados</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">Desempenho final de {userName || "..."}</h1>
        <p className="mt-1 text-sm text-slate-500">
          Esta tela mostra apenas atividades concluídas.
        </p>
      </div>

      {loading ? (
        <div className="flex justify-center py-14">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : results.length === 0 ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <BarChart3 size={40} className="mx-auto mb-4 text-slate-300" />
          <p className="text-slate-600">Nenhum resultado final disponível ainda.</p>
          <p className="mt-1 text-sm text-slate-400">Conclua uma atividade para ver seu desempenho aqui.</p>
          <Link
            href="/student"
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            Voltar para atividades
            <ArrowRight size={14} />
          </Link>
        </div>
      ) : (
        <div className="space-y-8">
          <section className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-3xl border border-emerald-100 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-500">Concluídas</p>
              <p className="mt-2 text-3xl font-bold text-slate-900">{results.length}</p>
            </div>
            <div className="rounded-3xl border border-blue-100 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-blue-500">Média geral</p>
              <p className="mt-2 text-3xl font-bold text-slate-900">{overall ?? "--"}%</p>
            </div>
            <div className="rounded-3xl border border-amber-100 bg-white p-5 shadow-sm">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-500">Disciplinas</p>
              <p className="mt-2 text-3xl font-bold text-slate-900">{disciplineGroups.length}</p>
            </div>
          </section>

          <section className="space-y-5">
            {disciplineGroups.map((group) => {
              const theme = getDisciplineTheme(group.label);

              return (
              <div key={group.id} id={group.id} className={clsx("space-y-3 scroll-mt-24 rounded-[2rem] border p-4", theme.border, theme.softBg)}>
                <div className="flex items-center gap-3">
                  <div className={clsx("flex h-12 w-12 items-center justify-center rounded-2xl text-lg font-black text-white shadow-sm", theme.accent)}>
                    {theme.icon}
                  </div>
                  <div>
                    <h2 className={clsx("text-base font-semibold", theme.text)}>{group.label}</h2>
                    <p className="text-xs text-slate-500">{group.activities.length} resultado(s)</p>
                  </div>
                </div>

                <div className="grid gap-3">
                  {group.activities.map((result) => (
                    <Link
                      key={result.id}
                      href={`/student/activities/${result.adaptation_id}`}
                      className={clsx("rounded-3xl border bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md", theme.border)}
                    >
                      <div className="flex items-center gap-4">
                        <div className={clsx("flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl font-bold", theme.softBg, theme.text)}>
                          {result.percentage ?? "--"}%
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <p className="truncate font-semibold text-slate-900">{result.title || "Atividade"}</p>
                            <span className={clsx("rounded-full px-2 py-0.5 text-xs font-medium", theme.badge)}>
                              {result.discipline || "Sem disciplina"}
                            </span>
                            {result.story?.title && (
                              <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">
                                {result.story.title}
                              </span>
                            )}
                          </div>
                          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                            <span className="inline-flex items-center gap-1">
                              <Trophy size={12} />
                              {result.score ?? 0} / {result.max_score ?? 0}
                            </span>
                            <span className="inline-flex items-center gap-1">
                              <Clock size={12} />
                              {result.finished_at ? new Date(result.finished_at).toLocaleDateString("pt-BR") : "sem data"}
                            </span>
                          </div>
                        </div>
                        <ArrowRight size={16} className="text-slate-400" />
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
              );
            })}
          </section>
        </div>
      )}
    </StudentLayout>
  );
}
