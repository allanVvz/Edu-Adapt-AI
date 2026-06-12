"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import AdminLayout from "@/components/layout/AdminLayout";
import { getUser } from "@/lib/auth";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { Users, GraduationCap, BookOpen, Shield, ChevronDown, ChevronRight, Check, X, RefreshCw, Loader2 } from "lucide-react";
import clsx from "clsx";

// ─── Types ────────────────────────────────────────────────────────────────────
interface UserData {
  id: string;
  name: string;
  email: string;
  role: "admin" | "teacher" | "student";
  is_active: boolean;
  created_at: string;
}

interface AdaptationData {
  id: string;
  status: string;
  version: number;
  created_at: string;
}

interface ActivityData {
  activity: { id: string; title: string; discipline: string | null };
  adaptations: AdaptationData[];
}

interface StudentData {
  student: { id: string; user_id: string; name: string; email: string; school_year: string | null };
  activities: ActivityData[];
}

interface TeacherData {
  teacher: { id: string; name: string; email: string };
  students: StudentData[];
}

interface OverviewData {
  teachers: TeacherData[];
  unassigned_students: Array<{ id: string; name: string; email: string; school_year: string | null }>;
}

// ─── Constants ────────────────────────────────────────────────────────────────
const ROLE_PAGES = [
  { page: "Dashboard", path: "/dashboard", admin: true, teacher: true, student: false },
  { page: "Atividades", path: "/activities", admin: true, teacher: true, student: false },
  { page: "Validações pendentes", path: "/validations", admin: true, teacher: true, student: false },
  { page: "Alunos", path: "/students", admin: true, teacher: true, student: false },
  { page: "Perfis pedagógicos", path: "/student-profiles", admin: true, teacher: true, student: false },
  { page: "Configurações", path: "/settings", admin: true, teacher: true, student: false },
  { page: "Chaves de API", path: "/settings/api-keys", admin: true, teacher: true, student: false },
  { page: "Integrações", path: "/settings/integrations", admin: true, teacher: false, student: false },
  { page: "Permissões", path: "/permissions", admin: true, teacher: false, student: false },
  { page: "Área do aluno", path: "/student", admin: false, teacher: false, student: true },
  { page: "Atividade interativa", path: "/student/activities/[id]", admin: false, teacher: false, student: true },
];

const ROLE_COLORS: Record<string, string> = {
  admin: "bg-red-100 text-red-700",
  teacher: "bg-purple-100 text-purple-700",
  student: "bg-green-100 text-green-700",
};

const STATUS_COLORS: Record<string, string> = {
  published: "bg-green-100 text-green-700",
  approved: "bg-blue-100 text-blue-700",
  review: "bg-yellow-100 text-yellow-700",
  rejected: "bg-red-100 text-red-500",
  draft: "bg-gray-100 text-gray-500",
};

const TABS = [
  { id: "matrix", label: "Matriz de Permissões", icon: Shield },
  { id: "users", label: "Usuários", icon: Users },
  { id: "relationships", label: "Prof. → Alunos", icon: GraduationCap },
  { id: "activities", label: "Alunos → Atividades", icon: BookOpen },
] as const;

type TabId = (typeof TABS)[number]["id"];

// ─── Sub-components ────────────────────────────────────────────────────────────
function StatusDot({ ok }: { ok: boolean }) {
  return ok
    ? <Check size={13} className="text-green-600 mx-auto" />
    : <X size={13} className="text-gray-300 mx-auto" />;
}

// ─── Page ─────────────────────────────────────────────────────────────────────
export default function PermissionsPage() {
  const router = useRouter();
  const [tab, setTab] = useState<TabId>("matrix");
  const [users, setUsers] = useState<UserData[]>([]);
  const [overview, setOverview] = useState<OverviewData | null>(null);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [loadingOverview, setLoadingOverview] = useState(false);
  const [savingUserId, setSavingUserId] = useState<string | null>(null);
  const [expandedTeachers, setExpandedTeachers] = useState<Set<string>>(new Set());
  const [expandedStudents, setExpandedStudents] = useState<Set<string>>(new Set());
  const [assigningStudentId, setAssigningStudentId] = useState<string | null>(null);
  const [assignTeacherId, setAssignTeacherId] = useState("");

  useEffect(() => {
    const user = getUser();
    if (!user || user.role !== "admin") {
      router.replace("/dashboard");
      return;
    }
    loadUsers();
    loadOverview();
  }, []);

  async function loadUsers() {
    setLoadingUsers(true);
    try {
      const { data } = await api.get("/admin/users");
      setUsers(data);
    } catch {
      toast.error("Erro ao carregar usuários.");
    } finally {
      setLoadingUsers(false);
    }
  }

  async function loadOverview() {
    setLoadingOverview(true);
    try {
      const { data } = await api.get("/admin/overview");
      setOverview(data);
      // Auto-expand all teachers
      setExpandedTeachers(new Set(data.teachers.map((t: TeacherData) => t.teacher.id)));
    } catch {
      toast.error("Erro ao carregar visão geral.");
    } finally {
      setLoadingOverview(false);
    }
  }

  async function updateUser(userId: string, updates: { role?: string; is_active?: boolean }) {
    setSavingUserId(userId);
    try {
      await api.put(`/admin/users/${userId}`, updates);
      toast.success("Usuário atualizado.");
      setUsers((prev) => prev.map((u) => u.id === userId ? { ...u, ...updates } as UserData : u));
    } catch {
      toast.error("Erro ao atualizar usuário.");
    } finally {
      setSavingUserId(null);
    }
  }

  async function assignTeacher(studentId: string) {
    if (!assignTeacherId) { toast.error("Selecione um professor."); return; }
    try {
      await api.post("/admin/assign-teacher", { teacher_id: assignTeacherId, student_id: studentId });
      toast.success("Professor atribuído.");
      setAssigningStudentId(null);
      setAssignTeacherId("");
      loadOverview();
    } catch {
      toast.error("Erro ao atribuir professor.");
    }
  }

  async function unassignTeacher(teacherId: string, studentId: string) {
    try {
      await api.delete(`/admin/assign-teacher?teacher_id=${teacherId}&student_id=${studentId}`);
      toast.success("Vínculo removido.");
      loadOverview();
    } catch {
      toast.error("Erro ao remover vínculo.");
    }
  }

  const teachers = users.filter((u) => u.role === "teacher");

  return (
    <AdminLayout>
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Permissões e Atribuições</h1>
        <p className="text-sm text-gray-500 mt-1">Gerencie usuários, papéis e relacionamentos entre professores e alunos.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 overflow-x-auto pb-1">
        {TABS.map(({ id, label, icon: Icon }) => (
          <button key={id} onClick={() => setTab(id)}
            className={clsx("flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg whitespace-nowrap transition-colors", {
              "bg-blue-600 text-white": tab === id,
              "bg-white border border-gray-200 text-gray-600 hover:bg-gray-50": tab !== id,
            })}>
            <Icon size={14} /> {label}
          </button>
        ))}
      </div>

      {/* ── Tab: Matriz ────────────────────────────────────────────────── */}
      {tab === "matrix" && (
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="px-5 py-4 border-b border-gray-100">
            <h2 className="font-semibold text-gray-700">Matriz de acesso por hierarquia</h2>
            <p className="text-xs text-gray-400 mt-0.5">Quais páginas cada nível de usuário pode acessar.</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 bg-gray-50">
                  <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wider">Página / Rota</th>
                  <th className="text-center px-5 py-3 text-xs font-semibold text-red-500 uppercase tracking-wider">Admin</th>
                  <th className="text-center px-5 py-3 text-xs font-semibold text-purple-600 uppercase tracking-wider">Professor</th>
                  <th className="text-center px-5 py-3 text-xs font-semibold text-green-600 uppercase tracking-wider">Aluno</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-50">
                {ROLE_PAGES.map(({ page, path, admin, teacher, student }) => (
                  <tr key={path} className="hover:bg-gray-50">
                    <td className="px-5 py-3">
                      <p className="font-medium text-gray-700">{page}</p>
                      <p className="text-xs text-gray-400 font-mono">{path}</p>
                    </td>
                    <td className="px-5 py-3 text-center"><StatusDot ok={admin} /></td>
                    <td className="px-5 py-3 text-center"><StatusDot ok={teacher} /></td>
                    <td className="px-5 py-3 text-center"><StatusDot ok={student} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Tab: Usuários ──────────────────────────────────────────────── */}
      {tab === "users" && (
        <div className="bg-white rounded-xl border border-gray-200">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 className="font-semibold text-gray-700">Gerenciar usuários</h2>
              <p className="text-xs text-gray-400 mt-0.5">Altere papéis e status de acesso de qualquer email cadastrado.</p>
            </div>
            <button onClick={loadUsers} disabled={loadingUsers}
              className="flex items-center gap-1.5 text-xs text-gray-500 hover:text-gray-700 border border-gray-200 px-3 py-1.5 rounded-lg">
              {loadingUsers ? <Loader2 size={13} className="animate-spin" /> : <RefreshCw size={13} />} Atualizar
            </button>
          </div>

          {loadingUsers ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin h-6 w-6 border-4 border-blue-500 border-t-transparent rounded-full" />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500">Nome</th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500">Email</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500">Papel</th>
                    <th className="text-center px-5 py-3 text-xs font-semibold text-gray-500">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {users.map((u) => (
                    <tr key={u.id} className="hover:bg-gray-50">
                      <td className="px-5 py-3 font-medium text-gray-800">{u.name}</td>
                      <td className="px-5 py-3 text-gray-500 text-xs font-mono">{u.email}</td>
                      <td className="px-5 py-3 text-center">
                        <div className="flex items-center justify-center gap-1">
                          <div className="relative">
                            <select
                              value={u.role}
                              onChange={(e) => updateUser(u.id, { role: e.target.value })}
                              disabled={savingUserId === u.id}
                              className={clsx(
                                "text-xs font-medium rounded-full px-3 py-1 border-0 cursor-pointer appearance-none pr-6",
                                ROLE_COLORS[u.role]
                              )}
                            >
                              <option value="admin">admin</option>
                              <option value="teacher">professor</option>
                              <option value="student">aluno</option>
                            </select>
                            <ChevronDown size={10} className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none opacity-60" />
                          </div>
                          {savingUserId === u.id && <Loader2 size={12} className="animate-spin text-blue-500" />}
                        </div>
                      </td>
                      <td className="px-5 py-3 text-center">
                        <button
                          onClick={() => updateUser(u.id, { is_active: !u.is_active })}
                          disabled={savingUserId === u.id}
                          className={clsx(
                            "text-xs font-medium px-3 py-1 rounded-full transition-colors",
                            u.is_active
                              ? "bg-green-100 text-green-700 hover:bg-green-200"
                              : "bg-gray-100 text-gray-400 hover:bg-gray-200"
                          )}
                        >
                          {u.is_active ? "Ativo" : "Inativo"}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Tab: Professores → Alunos ──────────────────────────────────── */}
      {tab === "relationships" && (
        <div className="space-y-4">
          {loadingOverview ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin h-6 w-6 border-4 border-blue-500 border-t-transparent rounded-full" />
            </div>
          ) : overview ? (
            <>
              {overview.teachers.map((t) => (
                <div key={t.teacher.id} className="bg-white rounded-xl border border-gray-200">
                  <button
                    className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors rounded-xl"
                    onClick={() => setExpandedTeachers((prev) => {
                      const next = new Set(prev);
                      next.has(t.teacher.id) ? next.delete(t.teacher.id) : next.add(t.teacher.id);
                      return next;
                    })}
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-700 font-bold text-sm">
                        {t.teacher.name[0]}
                      </div>
                      <div className="text-left">
                        <p className="font-semibold text-gray-800 text-sm">{t.teacher.name}</p>
                        <p className="text-xs text-gray-400">{t.teacher.email}</p>
                      </div>
                      <span className="text-xs bg-purple-50 text-purple-600 rounded-full px-2 py-0.5">
                        {t.students.length} aluno{t.students.length !== 1 ? "s" : ""}
                      </span>
                    </div>
                    <ChevronDown size={16} className={clsx("text-gray-400 transition-transform", expandedTeachers.has(t.teacher.id) && "rotate-180")} />
                  </button>

                  {expandedTeachers.has(t.teacher.id) && (
                    <div className="border-t border-gray-100 divide-y divide-gray-50">
                      {t.students.length === 0 ? (
                        <p className="text-sm text-gray-400 px-5 py-4">Nenhum aluno atribuído a este professor.</p>
                      ) : (
                        t.students.map((s) => (
                          <div key={s.student.id} className="px-5 py-3 flex items-center justify-between">
                            <div className="flex items-center gap-3">
                              <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-xs">
                                {s.student.name[0]}
                              </div>
                              <div>
                                <p className="text-sm font-medium text-gray-700">{s.student.name}</p>
                                <p className="text-xs text-gray-400">{s.student.email}</p>
                              </div>
                              {s.student.school_year && (
                                <span className="text-xs bg-gray-100 text-gray-500 rounded-full px-2 py-0.5">{s.student.school_year}</span>
                              )}
                            </div>
                            <button
                              onClick={() => unassignTeacher(t.teacher.id, s.student.id)}
                              className="text-xs text-red-500 hover:text-red-700 border border-red-100 hover:border-red-300 px-2 py-1 rounded-lg transition-colors"
                            >
                              Remover vínculo
                            </button>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              ))}

              {/* Unassigned students */}
              {overview.unassigned_students.length > 0 && (
                <div className="bg-white rounded-xl border border-orange-200">
                  <div className="px-5 py-4 border-b border-orange-100">
                    <h3 className="font-semibold text-orange-700 text-sm">
                      Alunos sem professor atribuído ({overview.unassigned_students.length})
                    </h3>
                  </div>
                  <div className="divide-y divide-gray-50">
                    {overview.unassigned_students.map((s) => (
                      <div key={s.id} className="px-5 py-3 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="w-7 h-7 rounded-full bg-orange-100 flex items-center justify-center text-orange-700 font-bold text-xs">
                            {s.name[0]}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-gray-700">{s.name}</p>
                            <p className="text-xs text-gray-400">{s.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          {assigningStudentId === s.id ? (
                            <>
                              <div className="relative">
                                <select
                                  value={assignTeacherId}
                                  onChange={(e) => setAssignTeacherId(e.target.value)}
                                  className="text-xs border border-gray-200 rounded-lg px-2 py-1.5 pr-6 appearance-none"
                                >
                                  <option value="">Selecionar professor...</option>
                                  {teachers.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                                </select>
                                <ChevronDown size={10} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none" />
                              </div>
                              <button onClick={() => assignTeacher(s.id)}
                                className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-2 py-1.5 rounded-lg">
                                Confirmar
                              </button>
                              <button onClick={() => { setAssigningStudentId(null); setAssignTeacherId(""); }}
                                className="text-xs text-gray-500 border border-gray-200 px-2 py-1.5 rounded-lg">
                                Cancelar
                              </button>
                            </>
                          ) : (
                            <button onClick={() => setAssigningStudentId(s.id)}
                              className="text-xs text-blue-600 border border-blue-200 px-2 py-1.5 rounded-lg hover:bg-blue-50">
                              Atribuir professor
                            </button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="text-gray-400 text-sm">Sem dados.</p>
          )}
        </div>
      )}

      {/* ── Tab: Alunos → Atividades ───────────────────────────────────── */}
      {tab === "activities" && (
        <div className="space-y-4">
          {loadingOverview ? (
            <div className="flex justify-center py-12">
              <div className="animate-spin h-6 w-6 border-4 border-blue-500 border-t-transparent rounded-full" />
            </div>
          ) : overview ? (
            overview.teachers.flatMap((t) => t.students).map((s) => (
              <div key={s.student.id} className="bg-white rounded-xl border border-gray-200">
                <button
                  className="w-full px-5 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors rounded-xl"
                  onClick={() => setExpandedStudents((prev) => {
                    const next = new Set(prev);
                    next.has(s.student.id) ? next.delete(s.student.id) : next.add(s.student.id);
                    return next;
                  })}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-sm">
                      {s.student.name[0]}
                    </div>
                    <div className="text-left">
                      <p className="font-semibold text-gray-800 text-sm">{s.student.name}</p>
                      <p className="text-xs text-gray-400">{s.student.email}</p>
                    </div>
                    <span className="text-xs bg-blue-50 text-blue-600 rounded-full px-2 py-0.5">
                      {s.activities.length} atividade{s.activities.length !== 1 ? "s" : ""}
                    </span>
                    {s.activities.some((a) => a.adaptations.some((ad) => ad.status === "published")) && (
                      <span className="text-xs bg-green-50 text-green-600 rounded-full px-2 py-0.5">
                        {s.activities.filter((a) => a.adaptations.some((ad) => ad.status === "published")).length} visível{
                          s.activities.filter((a) => a.adaptations.some((ad) => ad.status === "published")).length !== 1 ? "is" : ""
                        }
                      </span>
                    )}
                  </div>
                  <ChevronRight size={16} className={clsx("text-gray-400 transition-transform", expandedStudents.has(s.student.id) && "rotate-90")} />
                </button>

                {expandedStudents.has(s.student.id) && (
                  <div className="border-t border-gray-100">
                    {s.activities.length === 0 ? (
                      <p className="text-sm text-gray-400 px-5 py-4">Nenhuma atividade associada a este aluno.</p>
                    ) : (
                      <div className="divide-y divide-gray-50">
                        {s.activities.map((a) => (
                          <div key={a.activity.id} className="px-5 py-3">
                            <div className="flex items-center gap-2 mb-2">
                              <p className="text-sm font-medium text-gray-800">{a.activity.title}</p>
                              {a.activity.discipline && (
                                <span className="text-xs bg-gray-100 text-gray-500 rounded-full px-2 py-0.5">{a.activity.discipline}</span>
                              )}
                            </div>
                            <div className="flex flex-wrap gap-2">
                              {a.adaptations.map((ad) => (
                                <div key={ad.id} className="flex items-center gap-1.5 border border-gray-100 rounded-lg px-2 py-1">
                                  <span className="text-xs text-gray-500">v{ad.version}</span>
                                  <span className={clsx("text-xs font-medium px-1.5 py-0.5 rounded-full", STATUS_COLORS[ad.status] ?? "bg-gray-100 text-gray-500")}>
                                    {ad.status}
                                  </span>
                                </div>
                              ))}
                              {a.adaptations.length === 0 && (
                                <span className="text-xs text-gray-400">Sem adaptações</span>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          ) : null}
        </div>
      )}
    </AdminLayout>
  );
}
