"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import clsx from "clsx";
import StudentLayout from "@/components/layout/StudentLayout";
import StudentHeaderMenu from "@/components/layout/StudentHeaderMenu";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import { ArrowLeft, ArrowRight, Clock, Download, Home, LibraryBig } from "lucide-react";
import {
  getDisciplineHref,
  getDisciplineTheme,
  groupActivitiesByDiscipline,
  type StudentActivityCard,
} from "@/lib/student-area";

export default function StudentDisciplinePage() {
  const { discipline } = useParams<{ discipline: string }>();
  const router = useRouter();
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
  const currentGroup = disciplineGroups.find((group) => group.id === discipline);
  const title = currentGroup?.label ?? "Disciplina";
  const theme = getDisciplineTheme(currentGroup?.label ?? discipline);

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
        />
      }
    >
      {loading ? (
        <div className="flex justify-center py-14">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
        </div>
      ) : !currentGroup ? (
        <div className="rounded-3xl border border-slate-200 bg-white p-10 text-center shadow-sm">
          <p className="text-lg font-bold text-slate-900">Disciplina não encontrada.</p>
          <Link
            href="/student"
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-blue-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-blue-700"
          >
            <Home size={14} />
            Voltar para home
          </Link>
        </div>
      ) : (
        <div className="space-y-6">
          <section className={clsx("overflow-hidden rounded-[2rem] border bg-white shadow-sm", theme.border)}>
            <div className={clsx("p-6", theme.softBg)}>
              <Link
                href="/student"
                className="mb-5 inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1.5 text-sm font-semibold text-slate-700 shadow-sm transition-colors hover:bg-white"
              >
                <ArrowLeft size={14} />
                Voltar para home
              </Link>
              <div className="flex items-center gap-4">
                <div className={clsx("flex h-20 w-20 items-center justify-center rounded-3xl text-2xl font-black text-white shadow-sm", theme.accent)}>
                  {theme.icon}
                </div>
                <div>
                  <p className={clsx("text-xs font-semibold uppercase tracking-[0.22em]", theme.text)}>
                    Disciplina
                  </p>
                  <h1 className="mt-1 text-4xl font-black tracking-tight text-slate-950">{title}</h1>
                  <p className="mt-2 text-sm text-slate-600">
                    {currentGroup.activities.length} atividade(s) organizadas nesta área.
                  </p>
                </div>
              </div>
            </div>
          </section>

          <section className="grid gap-3">
            {currentGroup.activities.map((activity, index) => (
              <Link
                key={activity.id}
                href={`/student/activities/${activity.id}`}
                className={clsx("rounded-3xl border bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md", theme.border)}
              >
                <div className="flex items-center gap-4">
                  <div className={clsx("flex h-12 w-12 flex-shrink-0 items-center justify-center rounded-2xl font-bold", theme.softBg, theme.text)}>
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
          </section>
        </div>
      )}
    </StudentLayout>
  );
}
