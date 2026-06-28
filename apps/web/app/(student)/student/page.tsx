"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import StudentLayout from "@/components/layout/StudentLayout";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import { BookOpen, Clock, Download } from "lucide-react";

interface ActivityItem {
  id: string;
  activity_id: string;
  title: string | null;
  status: string;
  created_at: string;
}

export default function StudentPage() {
  const router = useRouter();
  const [userName, setUserName] = useState("");
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const user = getUser();
    if (!user) { router.replace("/login"); return; }
    if (user.role !== "student") { router.replace("/dashboard"); return; }
    setUserName(user.name);

    api.get("/student/activities")
      .then((r) => setActivities(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

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

  const exportButton = (
    <button
      onClick={handleExportAllPDF}
      disabled={exporting || activities.length === 0}
      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
    >
      <Download size={14} />
      {exporting ? "Gerando..." : "Exportar PDF"}
    </button>
  );

  return (
    <StudentLayout headerAction={exportButton}>
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Olá, {userName || "..."}! 👋</h1>
        <p className="text-sm text-gray-500">Suas atividades de hoje estão aqui.</p>
      </div>

      {loading ? (
        <div className="flex justify-center py-10">
          <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
        </div>
      ) : activities.length === 0 ? (
        <div className="bg-white rounded-2xl border border-blue-100 p-10 text-center">
          <BookOpen size={40} className="mx-auto mb-4 text-blue-300" />
          <p className="text-gray-500">Nenhuma atividade disponível ainda.</p>
          <p className="text-sm text-gray-400 mt-1">Seu professor vai publicar atividades aqui em breve.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {activities.map((a, idx) => (
            <button
              key={a.id}
              onClick={() => router.push(`/student/activities/${a.id}`)}
              className="bg-white rounded-2xl border border-blue-100 p-5 text-left hover:border-blue-300 hover:shadow-sm transition-all"
            >
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-100 flex items-center justify-center text-blue-700 font-bold">
                  {idx + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-900">{a.title || `Atividade ${idx + 1}`}</p>
                  <div className="flex items-center gap-1 mt-0.5 text-xs text-gray-400">
                    <Clock size={11} />
                    <span>{new Date(a.created_at).toLocaleDateString("pt-BR")}</span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}
    </StudentLayout>
  );
}
