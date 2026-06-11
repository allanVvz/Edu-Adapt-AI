"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { AuthUser, clearAuth } from "@/lib/auth";
import { ChevronDown, Settings, Key, LogOut } from "lucide-react";

const ROLE_LABELS: Record<string, string> = {
  admin: "Administrador",
  teacher: "Professor",
  student: "Aluno",
};

export default function UserDropdown({ user }: { user: AuthUser }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);

  function logout() {
    clearAuth();
    router.push("/login");
  }

  return (
    <div className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 bg-white border border-gray-200 rounded-lg px-3 py-2 text-sm hover:bg-gray-50 transition-colors"
      >
        <div className="w-7 h-7 rounded-full bg-blue-600 flex items-center justify-center text-white font-bold text-xs">
          {user.name[0].toUpperCase()}
        </div>
        <span className="font-medium text-gray-700 max-w-[120px] truncate">{user.name}</span>
        <ChevronDown size={14} className="text-gray-400" />
      </button>

      {open && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setOpen(false)} />
          <div className="absolute right-0 top-full mt-1 z-20 bg-white border border-gray-200 rounded-xl shadow-lg w-56 py-2">
            <div className="px-4 py-3 border-b border-gray-100">
              <p className="font-semibold text-sm text-gray-900">{user.name}</p>
              <p className="text-xs text-gray-500">{user.email}</p>
              <span className="inline-block mt-1 text-xs bg-blue-100 text-blue-700 rounded-full px-2 py-0.5">
                {ROLE_LABELS[user.role] || user.role}
              </span>
            </div>

            <button
              onClick={() => { setOpen(false); router.push("/settings"); }}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
            >
              <Settings size={14} /> Configurações
            </button>

            {(user.role === "admin" || user.role === "teacher") && (
              <button
                onClick={() => { setOpen(false); router.push("/settings/api-keys"); }}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
              >
                <Key size={14} /> Chaves de API
              </button>
            )}

            <div className="border-t border-gray-100 mt-1 pt-1">
              <button
                onClick={logout}
                className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                <LogOut size={14} /> Sair
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
