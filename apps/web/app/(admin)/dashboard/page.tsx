"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AdminLayout from "@/components/layout/AdminLayout";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import { Users, BookOpen, BarChart3, Clock, AlertCircle } from "lucide-react";

interface DashboardData {
  total_students: number;
  total_activities: number;
  published_adaptations: number;
  pending_adaptations: number;
  avg_score: number | null;
  recent_attempts: Array<{
    id: string;
    student_id: string;
    activity_id: string;
    score: number | null;
    max_score: number | null;
    status: string;
    created_at: string;
  }>;
}

function StatCard({ label, value, icon: Icon, color }: {
  label: string; value: number | string; icon: React.ComponentType<{ size?: number }>; color: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 flex items-start gap-4">
      <div className={`p-2.5 rounded-lg ${color}`}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-2xl font-bold text-gray-900">{value ?? "—"}</p>
        <p className="text-sm text-gray-500">{label}</p>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const router = useRouter();
  const user = getUser();
  const [data, setData] = useState<DashboardData | null>(null);

  useEffect(() => {
    if (!user || user.role === "student") { router.replace("/student"); return; }
    api.get("/dashboard/teacher").then((r) => setData(r.data)).catch(() => {});
  }, []);

  return (
    <AdminLayout>
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Olá, {user?.name} 👋</h1>
        <p className="text-sm text-gray-500">Aqui está o resumo das suas atividades.</p>
      </div>

      {data ? (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard label="Alunos" value={data.total_students} icon={Users} color="bg-blue-100 text-blue-700" />
            <StatCard label="Atividades" value={data.total_activities} icon={BookOpen} color="bg-green-100 text-green-700" />
            <StatCard
              label="Adaptações publicadas"
              value={data.published_adaptations}
              icon={BarChart3}
              color="bg-purple-100 text-purple-700"
            />
            <StatCard
              label="Pendentes de revisão"
              value={data.pending_adaptations}
              icon={AlertCircle}
              color="bg-yellow-100 text-yellow-700"
            />
          </div>

          {data.avg_score !== null && (
            <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
              <p className="text-sm font-medium text-gray-500 mb-1">Média dos alunos</p>
              <p className="text-3xl font-bold text-blue-700">
                {data.avg_score?.toFixed(1)} <span className="text-base text-gray-400">/ 4.0</span>
              </p>
            </div>
          )}

          <div className="bg-white rounded-xl border border-gray-200">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2">
              <Clock size={16} className="text-gray-400" />
              <h2 className="font-semibold text-gray-700">Últimas tentativas</h2>
            </div>
            {data.recent_attempts.length === 0 ? (
              <p className="text-sm text-gray-400 p-5">Nenhuma tentativa ainda.</p>
            ) : (
              <div className="divide-y divide-gray-50">
                {data.recent_attempts.map((a) => (
                  <div key={a.id} className="px-5 py-3 flex items-center justify-between text-sm">
                    <span className="text-gray-600 font-mono text-xs">{a.activity_id.slice(0, 8)}…</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${a.status === "completed" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"}`}>
                      {a.status === "completed" ? "Concluída" : a.status}
                    </span>
                    <span className="text-gray-700 font-medium">
                      {a.score !== null ? `${a.score} / ${a.max_score}` : "—"}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="flex justify-center py-20">
          <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
        </div>
      )}
    </AdminLayout>
  );
}
