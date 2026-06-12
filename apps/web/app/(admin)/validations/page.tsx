"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import AdminLayout from "@/components/layout/AdminLayout";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import { ClipboardCheck, ChevronRight, CheckCircle, ShieldCheck } from "lucide-react";
import clsx from "clsx";

interface PendingAdaptation {
  id: string;
  activity: { id: string; title: string } | null;
  profile: { id: string; name: string } | null;
  generated_by: string;
  status: string;
  version: number;
  created_at: string;
}

export default function ValidationsPage() {
  const router = useRouter();
  const [isAdmin, setIsAdmin] = useState(false);
  const [list, setList] = useState<PendingAdaptation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const user = getUser();
    if (!user || user.role === "student") {
      router.replace("/student");
      return;
    }
    setIsAdmin(user.role === "admin");
    api.get("/adaptations?status=review")
      .then((r) => setList(r.data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <AdminLayout>
      <div className="mb-6">
        <div className="flex items-center gap-2">
          <ClipboardCheck size={20} className="text-yellow-600" />
          <h1 className="text-xl font-bold text-gray-900">Validações pendentes</h1>
          {list.length > 0 && (
            <span className="bg-yellow-100 text-yellow-700 text-xs font-bold rounded-full px-2 py-0.5">{list.length}</span>
          )}
        </div>
        <p className="text-sm text-gray-500 mt-1">Adaptações geradas aguardando revisão do professor ou admin.</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-200 mb-6">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin h-8 w-8 border-4 border-yellow-500 border-t-transparent rounded-full" />
          </div>
        ) : list.length === 0 ? (
          <div className="flex flex-col items-center py-12 text-gray-400">
            <CheckCircle size={32} className="text-green-400 mb-2" />
            <p className="text-sm">Nenhuma adaptação pendente de validação.</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {list.map((a) => (
              <Link key={a.id} href={`/adaptations/${a.id}/review`}
                className="flex items-center justify-between px-5 py-4 hover:bg-gray-50 transition-colors group">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">
                    {a.activity?.title || "Atividade sem título"}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    {a.profile && (
                      <span className="text-xs text-purple-600 bg-purple-50 rounded-full px-2 py-0.5">
                        {a.profile.name}
                      </span>
                    )}
                    <span className="text-xs text-gray-400">v{a.version}</span>
                    <span className="text-xs text-gray-400">via {a.generated_by}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3 ml-4">
                  <span className={clsx("text-xs font-medium px-2 py-0.5 rounded-full", {
                    "bg-yellow-100 text-yellow-700": a.status === "review",
                    "bg-gray-100 text-gray-500": a.status === "draft",
                  })}>
                    {a.status === "review" ? "Aguardando revisão" : a.status}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(a.created_at).toLocaleDateString("pt-BR")}
                  </span>
                  <ChevronRight size={16} className="text-gray-300 group-hover:text-gray-500 transition-colors" />
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {isAdmin && (
        <Link href="/permissions"
          className="flex items-center gap-3 bg-white border border-gray-200 rounded-xl px-5 py-4 hover:bg-blue-50 hover:border-blue-200 transition-colors group">
          <ShieldCheck size={20} className="text-blue-500" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-gray-800">Gerenciar permissões e atribuições</p>
            <p className="text-xs text-gray-400">Configure papéis de usuários, vínculos professor→aluno e visibilidade de atividades.</p>
          </div>
          <ChevronRight size={16} className="text-gray-300 group-hover:text-blue-400 transition-colors" />
        </Link>
      )}
    </AdminLayout>
  );
}
