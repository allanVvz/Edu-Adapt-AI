"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { Home } from "lucide-react";
import { AuthUser, getUser } from "@/lib/auth";
import UserDropdown from "./UserDropdown";

interface StudentLayoutProps {
  children: React.ReactNode;
  headerAction?: React.ReactNode;
}

export default function StudentLayout({ children, headerAction }: StudentLayoutProps) {
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    setUser(getUser());
  }, []);

  return (
    <div className="min-h-screen bg-blue-50">
      <header className="bg-white shadow-sm border-b border-blue-100">
        <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/student" className="flex items-center gap-2 text-blue-700 font-bold">
              <Home size={20} />
              <span>Minhas Atividades</span>
            </Link>
            {headerAction}
          </div>
          <div className="flex items-center gap-3">
            {user && <UserDropdown user={user} />}
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
