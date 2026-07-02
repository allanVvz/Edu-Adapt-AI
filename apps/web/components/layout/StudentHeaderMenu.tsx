"use client";

import { useState } from "react";
import Link from "next/link";
import { BarChart3, ChevronDown, Download, Home } from "lucide-react";
import clsx from "clsx";
import { getDisciplineTheme } from "@/lib/student-area";

interface DisciplineLink {
  id: string;
  label: string;
  href?: string;
}

interface StudentHeaderMenuProps {
  disciplines?: DisciplineLink[];
  onExportAll?: () => void;
  exportDisabled?: boolean;
  resultsHref?: string;
}

export default function StudentHeaderMenu({
  disciplines = [],
  onExportAll,
  exportDisabled = false,
  resultsHref = "/student/results",
}: StudentHeaderMenuProps) {
  const [open, setOpen] = useState(false);

  return (
    <div className="flex items-center gap-2">
      {onExportAll && (
        <button
          type="button"
          onClick={onExportAll}
          disabled={exportDisabled}
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-blue-200 bg-white text-blue-700 transition-colors hover:bg-blue-50 disabled:cursor-not-allowed disabled:opacity-50"
          aria-label="Exportar apostila"
          title="Exportar apostila"
        >
          <Download size={16} />
        </button>
      )}

      <Link
        href={resultsHref}
        className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-blue-200 bg-white text-blue-700 transition-colors hover:bg-blue-50"
        aria-label="Ver resultados"
        title="Ver resultados"
      >
        <BarChart3 size={16} />
      </Link>

      <Link
        href="/student"
        className="inline-flex h-10 items-center gap-2 rounded-xl border border-blue-200 bg-white px-3 text-sm font-semibold text-blue-700 transition-colors hover:bg-blue-50"
        aria-label="Voltar para home"
        title="Voltar para home"
      >
        <Home size={16} />
        <span className="hidden sm:inline">Home</span>
      </Link>

      {disciplines.length > 0 && (
        <div className="relative">
          <button
            type="button"
            onClick={() => setOpen((current) => !current)}
            className={clsx(
              "inline-flex h-10 items-center gap-2 rounded-xl border border-blue-200 bg-white px-3 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-50",
              open && "bg-blue-50",
            )}
            aria-haspopup="menu"
            aria-expanded={open}
          >
            <span>Disciplinas</span>
            <ChevronDown size={14} className="opacity-70" />
          </button>

          {open && (
            <>
              <button
                type="button"
                className="fixed inset-0 z-10 cursor-default"
                onClick={() => setOpen(false)}
                aria-label="Fechar menu de disciplinas"
              />
              <div className="absolute right-0 top-full z-20 mt-2 w-56 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lg">
                <div className="border-b border-slate-100 px-4 py-3">
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">Disciplinas</p>
                </div>
                <div className="max-h-80 overflow-auto py-2">
                  {disciplines.map((discipline) => {
                    const theme = getDisciplineTheme(discipline.label);

                    return (
                      <Link
                        key={discipline.id}
                        href={discipline.href ?? `/student/disciplines/${discipline.id}`}
                        onClick={() => setOpen(false)}
                        className="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-700 transition-colors hover:bg-slate-50"
                      >
                        <span className={clsx("h-2.5 w-2.5 rounded-full", theme.accent)} />
                        {discipline.label}
                      </Link>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
