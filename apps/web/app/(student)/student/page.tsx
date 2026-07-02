"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import clsx from "clsx";
import StudentLayout from "@/components/layout/StudentLayout";
import StudentHeaderMenu from "@/components/layout/StudentHeaderMenu";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import { ArrowRight, BookOpen, Clock, Download, LibraryBig } from "lucide-react";
import {
  getDisciplineHref,
  getDisciplineTheme,
  groupActivitiesByDiscipline,
  groupActivitiesByStory,
  type StudentActivityCard,
} from "@/lib/student-area";

export default function StudentPage() {
  const router = useRouter();
  const [userName, setUserName] = useState("");
  const [activities, setActivities] = useState<StudentActivityCard[]>([]);
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
      .get("/student/activities")
      .then((r) => setActivities(r.data))
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

  const disciplineGroups = groupActivitiesByDiscipline(activities);
  const storyGroups = groupActivitiesByStory(activities);
  const headerAction = (
    <StudentHeaderMenu
      disciplines={disciplineGroups.map((group) => ({
        id: group.id,
        label: group.label,
        href: getDisciplineHref(group.id),
      }))}
      onExportAll={handleExportAllPDF}
      exportDisabled={exporting || loading}
    />
  );

  return (
    <StudentLayout headerAction={headerAction}>
      <div className="mb-8">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-500">Área do aluno</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">Olá, {userName || "..."}!</h1>
        <p className="mt-1 text-sm text-slate-500">Home central das atividades por contos e disciplinas.</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-14">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : activities.length === 0 ? (
        <div className="rounded-3xl border border-blue-100 bg-white p-10 text-center shadow-sm">
          <BookOpen size={40} className="mx-auto mb-4 text-blue-300" />
          <p className="text-gray-600">Nenhuma atividade disponível ainda.</p>
          <p className="mt-1 text-sm text-gray-400">Seu professor vai publicar atividades aqui em breve.</p>
        </div>
      ) : (
        <div className="space-y-8">
          {storyGroups.length > 0 && (
            <section className="space-y-4">
              <div className="flex items-end justify-between gap-4">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.22em] text-amber-500">Contos</p>
                  <h2 className="mt-1 text-lg font-bold text-slate-900">Blocos independentes</h2>
                </div>
                <p className="text-sm text-slate-500">{storyGroups.length} conto(s) vinculados</p>
              </div>

              <div className="grid gap-4">
                {storyGroups.map((story) => {
                  const firstActivity = story.activities[0];
                  const activityTitles = story.activities.map((activity) => activity.title || "Atividade");
                  const uniqueDisciplines = Array.from(
                    new Set(story.activities.map((activity) => activity.discipline || "Sem disciplina")),
                  );

                  return (
                    <div key={story.id} className="rounded-3xl border border-amber-100 bg-white p-5 shadow-sm">
                      <div className="flex items-start gap-4">
                        <div className="flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl bg-amber-100 text-amber-700">
                          <LibraryBig size={22} />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <h3 className="truncate text-base font-semibold text-slate-900">{story.label}</h3>
                            <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">
                              {story.activities.length} atividade(s)
                            </span>
                          </div>
                          <p className="mt-1 text-sm text-slate-500">{uniqueDisciplines.join(" · ")}</p>
                        </div>
                      </div>

                      <div className="mt-4 flex flex-wrap gap-2">
                        {activityTitles.map((title, index) => {
                          const activity = story.activities[index];
                          return (
                            <Link
                              key={activity.id}
                              href={`/student/activities/${activity.id}`}
                              className="inline-flex items-center gap-2 rounded-full border border-amber-100 bg-amber-50 px-3 py-1.5 text-sm font-medium text-amber-800 transition-colors hover:bg-amber-100"
                            >
                              <span className="font-semibold">{index + 1}.</span>
                              <span className="max-w-[220px] truncate">{title}</span>
                              <ArrowRight size={14} />
                            </Link>
                          );
                        })}
                      </div>

                      {firstActivity && (
                        <div className="mt-4 text-xs text-slate-500">
                          Primeira atividade publicada em {new Date(firstActivity.created_at).toLocaleDateString("pt-BR")}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          <section className="space-y-4">
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.22em] text-blue-500">Disciplinas</p>
                <h2 className="mt-1 text-lg font-bold text-slate-900">Atividades por área</h2>
              </div>
              <p className="text-sm text-slate-500">{activities.length} atividade(s)</p>
            </div>

            <div className="space-y-5">
              {disciplineGroups.map((group) => {
                const theme = getDisciplineTheme(group.label);

                return (
                <section key={group.id} id={group.id} className={clsx("scroll-mt-24 space-y-3 rounded-[2rem] border p-4", theme.border, theme.softBg)}>
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className={clsx("flex h-12 w-12 items-center justify-center rounded-2xl text-lg font-black text-white shadow-sm", theme.accent)}>
                        {theme.icon}
                      </div>
                      <div>
                        <h3 className={clsx("text-base font-semibold", theme.text)}>{group.label}</h3>
                        <p className="text-xs text-slate-500">{group.activities.length} atividade(s)</p>
                      </div>
                    </div>
                    <Link
                      href={getDisciplineHref(group.id)}
                      className={clsx("inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-bold transition-colors", theme.button)}
                    >
                      Abrir disciplina
                      <ArrowRight size={13} />
                    </Link>
                  </div>

                  <div className="grid gap-3">
                    {group.activities.map((activity, index) => (
                      <Link
                        key={activity.id}
                        href={`/student/activities/${activity.id}`}
                        className={clsx("rounded-3xl border bg-white p-5 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md", theme.border)}
                      >
                        <div className="flex items-center gap-4">
                          <div className={clsx("flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-2xl font-bold", theme.softBg, theme.text)}>
                            {index + 1}
                          </div>
                          <div className="min-w-0 flex-1">
                            <div className="flex flex-wrap items-center gap-2">
                              <p className="truncate font-semibold text-slate-900">{activity.title || `Atividade ${index + 1}`}</p>
                              {activity.has_result && (
                                <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">
                                  Concluída
                                </span>
                              )}
                              <span className={clsx("rounded-full px-2 py-0.5 text-xs font-medium", theme.badge)}>
                                {activity.discipline || "Sem disciplina"}
                              </span>
                            </div>
                            <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-slate-500">
                              <span className="inline-flex items-center gap-1">
                                <Clock size={12} />
                                {new Date(activity.created_at).toLocaleDateString("pt-BR")}
                              </span>
                              {activity.story?.title && (
                                <span className="inline-flex items-center gap-1">
                                  <LibraryBig size={12} />
                                  {activity.story.title}
                                </span>
                              )}
                              {activity.percentage !== null && activity.percentage !== undefined && (
                                <span className="inline-flex items-center gap-1 text-emerald-700">
                                  <Download size={12} />
                                  {activity.percentage}% finalizada
                                </span>
                              )}
                            </div>
                          </div>
                          <ArrowRight size={16} className="text-slate-400" />
                        </div>
                      </Link>
                    ))}
                  </div>
                </section>
              );
              })}
            </div>
          </section>

          <button
            onClick={handleExportAllPDF}
            disabled={exporting}
            className="w-full rounded-3xl border-2 border-dashed border-blue-300 px-4 py-4 font-semibold text-blue-700 transition-colors hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {exporting ? "Gerando apostila..." : `Exportar apostila completa (${activities.length} atividades)`}
          </button>
        </div>
      )}
    </StudentLayout>
  );
}
