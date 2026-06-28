"use client";
import { useEffect, useState } from "react";
import { BookOpen } from "lucide-react";
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
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 text-blue-700 font-bold">
            <BookOpen size={20} />
            <span>Minhas Atividades</span>
          </div>
          <div className="flex items-center gap-3">
            {headerAction}
            {user && <UserDropdown user={user} />}
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
