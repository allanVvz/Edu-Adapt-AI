"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, Users, BookOpen, UserCircle, Settings, Key, Puzzle, ChevronRight } from "lucide-react";
import { getUser } from "@/lib/auth";
import UserDropdown from "./UserDropdown";
import clsx from "clsx";

const nav = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/activities", label: "Atividades", icon: BookOpen },
  { href: "/students", label: "Alunos", icon: Users },
  { href: "/student-profiles", label: "Perfis", icon: UserCircle },
];

const navSettings = [
  { href: "/settings", label: "Configurações", icon: Settings },
  { href: "/settings/api-keys", label: "Chaves de API", icon: Key },
  { href: "/settings/integrations", label: "Integrações", icon: Puzzle },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const user = getUser();

  return (
    <div className="min-h-screen flex bg-gray-50">
      <aside className="w-60 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-4 py-5 border-b border-gray-100">
          <span className="text-lg font-bold text-blue-700">🎓 EduAdapt AI</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {nav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={clsx(
                "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                pathname === href
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100"
              )}
            >
              <Icon size={16} />
              {label}
            </Link>
          ))}

          <div className="pt-4 pb-1">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider px-3 mb-1">Configurações</p>
            {navSettings.map(({ href, label, icon: Icon }) => (
              <Link
                key={href}
                href={href}
                className={clsx(
                  "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  pathname === href
                    ? "bg-blue-50 text-blue-700"
                    : "text-gray-600 hover:bg-gray-100"
                )}
              >
                <Icon size={16} />
                {label}
              </Link>
            ))}
          </div>
        </nav>

        <div className="px-3 py-3 border-t border-gray-100 text-xs text-gray-400">
          v0.1.0
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
          <div className="flex items-center gap-1 text-sm text-gray-400">
            <ChevronRight size={14} />
            <span className="text-gray-700 font-medium capitalize">
              {pathname.split("/").filter(Boolean).join(" / ") || "Dashboard"}
            </span>
          </div>
          {user && <UserDropdown user={user} />}
        </header>

        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
