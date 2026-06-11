"use client";
import { BookOpen } from "lucide-react";
import { getUser } from "@/lib/auth";
import UserDropdown from "./UserDropdown";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  const user = getUser();

  return (
    <div className="min-h-screen bg-blue-50">
      <header className="bg-white shadow-sm border-b border-blue-100">
        <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2 text-blue-700 font-bold">
            <BookOpen size={20} />
            <span>Minhas Atividades</span>
          </div>
          {user && <UserDropdown user={user} />}
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-6">{children}</main>
    </div>
  );
}
