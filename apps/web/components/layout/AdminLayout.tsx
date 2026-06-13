"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Users, BookOpen, UserCircle,
  Settings, Key, Puzzle, ChevronRight, ClipboardCheck, ShieldCheck, Images,
} from "lucide-react";
import { getUser, AuthUser } from "@/lib/auth";
import UserDropdown from "./UserDropdown";
import clsx from "clsx";

type Role = "admin" | "teacher" | "student";

const navMain = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, roles: ["admin", "teacher"] as Role[] },
  { href: "/validations", label: "Validações", icon: ClipboardCheck, roles: ["admin", "teacher"] as Role[] },
  { href: "/activities", label: "Atividades", icon: BookOpen, roles: ["admin", "teacher"] as Role[] },
  { href: "/students", label: "Alunos", icon: Users, roles: ["admin", "teacher"] as Role[] },
  { href: "/student-profiles", label: "Perfis", icon: UserCircle, roles: ["admin", "teacher"] as Role[] },
  { href: "/permissions", label: "Permissões", icon: ShieldCheck, roles: ["admin"] as Role[] },
  { href: "/gallery", label: "Galeria", icon: Images, roles: ["admin", "teacher"] as Role[] },
];

const navSettings = [
  { href: "/settings", label: "Configurações", icon: Settings, roles: ["admin", "teacher"] as Role[] },
  { href: "/settings/api-keys", label: "Chaves de API", icon: Key, roles: ["admin", "teacher"] as Role[] },
  { href: "/settings/integrations", label: "Integrações", icon: Puzzle, roles: ["admin"] as Role[] },
];

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, []);

  const role = user?.role as Role | undefined;

  function NavLink({ href, label, icon: Icon }: { href: string; label: string; icon: React.ComponentType<{ size?: number | string }> }) {
    return (
      <Link
        href={href}
        className={clsx(
          "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
          pathname === href || pathname.startsWith(href + "/")
            ? "bg-blue-50 text-blue-700"
            : "text-gray-600 hover:bg-gray-100"
        )}
      >
        <Icon size={16} />
        {label}
      </Link>
    );
  }

  return (
    <div className="min-h-screen flex bg-gray-50">
      <aside className="w-60 bg-white border-r border-gray-200 flex flex-col">
        <div className="px-4 py-5 border-b border-gray-100">
          <span className="text-lg font-bold text-blue-700">EduAdapt AI</span>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {navMain
            .filter((item) => !role || item.roles.includes(role))
            .map(({ href, label, icon }) => (
              <NavLink key={href} href={href} label={label} icon={icon} />
            ))}

          <div className="pt-4 pb-1">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wider px-3 mb-1">Configurações</p>
            {navSettings
              .filter((item) => !role || item.roles.includes(role))
              .map(({ href, label, icon }) => (
                <NavLink key={href} href={href} label={label} icon={icon} />
              ))}
          </div>
        </nav>

        <div className="px-3 py-3 border-t border-gray-100 text-xs text-gray-400">
          v0.1.0
          {role && <span className="ml-1 text-gray-300">· {role}</span>}
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
          {/* Rendered only after client mount to prevent hydration mismatch */}
          {user && <UserDropdown user={user} />}
        </header>

        <main className="flex-1 p-6 overflow-auto">{children}</main>
      </div>
    </div>
  );
}
