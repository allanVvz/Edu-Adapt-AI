"use client";
import { useEffect, useState } from "react";
import AdminLayout from "@/components/layout/AdminLayout";
import api from "@/lib/api";
import toast from "react-hot-toast";
import { Plus, User, BookOpen } from "lucide-react";

interface Student {
  id: string;
  name: string;
  email: string;
  school_year: string | null;
  profile_name: string | null;
  learning_notes: string | null;
}

interface Profile {
  id: string;
  name: string;
}

export default function StudentsPage() {
  const [students, setStudents] = useState<Student[]>([]);
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    name: "", email: "", password: "", school_year: "", profile_id: "", learning_notes: "",
  });
  const [saving, setSaving] = useState(false);

  useEffect(() => { load(); }, []);

  async function load() {
    const [s, p] = await Promise.all([
      api.get("/students").catch(() => ({ data: [] })),
      api.get("/student-profiles").catch(() => ({ data: [] })),
    ]);
    setStudents(s.data);
    setProfiles(p.data);
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    try {
      await api.post("/students", form);
      toast.success("Aluno criado.");
      setShowModal(false);
      setForm({ name: "", email: "", password: "", school_year: "", profile_id: "", learning_notes: "" });
      load();
    } catch {
      toast.error("Erro ao criar aluno.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <AdminLayout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Alunos</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          <Plus size={15} /> Novo aluno
        </button>
      </div>

      {students.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center text-gray-400">
          <User size={32} className="mx-auto mb-3 opacity-30" />
          <p>Nenhum aluno cadastrado ainda.</p>
        </div>
      ) : (
        <div className="grid gap-3">
          {students.map((s) => (
            <div key={s.id} className="bg-white rounded-xl border border-gray-200 p-4 flex items-start gap-4">
              <div className="w-9 h-9 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-sm flex-shrink-0">
                {s.name[0]}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900">{s.name}</p>
                <p className="text-xs text-gray-400">{s.email}</p>
                <div className="flex gap-2 mt-1">
                  {s.school_year && (
                    <span className="text-xs bg-gray-100 text-gray-600 rounded-full px-2 py-0.5">{s.school_year}</span>
                  )}
                  {s.profile_name && (
                    <span className="text-xs bg-blue-100 text-blue-700 rounded-full px-2 py-0.5">{s.profile_name}</span>
                  )}
                </div>
                {s.learning_notes && (
                  <p className="text-xs text-gray-500 mt-1 line-clamp-1">{s.learning_notes}</p>
                )}
              </div>
              <BookOpen size={14} className="text-gray-300 flex-shrink-0 mt-1" />
            </div>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Novo aluno</h2>
            <form onSubmit={handleCreate} className="space-y-3">
              {[
                { label: "Nome", key: "name", type: "text", required: true },
                { label: "Email", key: "email", type: "email", required: true },
                { label: "Senha inicial", key: "password", type: "password", required: true },
                { label: "Ano escolar", key: "school_year", type: "text" },
              ].map(({ label, key, type, required }) => (
                <div key={key}>
                  <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
                  <input
                    type={type}
                    required={required}
                    value={(form as Record<string, string>)[key]}
                    onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                  />
                </div>
              ))}
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Perfil pedagógico</label>
                <select
                  value={form.profile_id}
                  onChange={(e) => setForm({ ...form, profile_id: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">Sem perfil</option>
                  {profiles.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Observações de aprendizagem</label>
                <textarea
                  value={form.learning_notes}
                  onChange={(e) => setForm({ ...form, learning_notes: e.target.value })}
                  rows={2}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm resize-none"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <button
                  type="submit"
                  disabled={saving}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 rounded-lg"
                >
                  {saving ? "Criando..." : "Criar aluno"}
                </button>
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 border border-gray-300 text-gray-600 text-sm py-2 rounded-lg">
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
