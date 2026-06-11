"use client";
import AdminLayout from "@/components/layout/AdminLayout";
import { ExternalLink } from "lucide-react";

export default function IntegrationsPage() {
  return (
    <AdminLayout>
      <h1 className="text-xl font-bold text-gray-900 mb-6">Integrações</h1>

      <div className="max-w-lg bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <h2 className="font-semibold text-gray-800">Vercel MCP</h2>
            <span className="inline-block mt-1 text-xs bg-gray-100 text-gray-500 rounded-full px-2 py-0.5">Não configurado</span>
          </div>
          <ExternalLink size={16} className="text-gray-300 mt-1" />
        </div>

        <p className="text-sm text-gray-500 mb-4">
          Configure a integração com o Vercel via MCP Claude para fazer deploy do frontend automaticamente.
          Consulte <code className="text-xs bg-gray-100 px-1 rounded">docs/vercel-mcp.md</code> para instruções.
        </p>

        <div className="space-y-3">
          {[
            { label: "Vercel Token", placeholder: "insira o token" },
            { label: "Project ID", placeholder: "prj_..." },
            { label: "MCP Server URL", placeholder: "https://..." },
          ].map(({ label, placeholder }) => (
            <div key={label}>
              <label className="block text-xs font-medium text-gray-600 mb-1">{label}</label>
              <input
                disabled
                placeholder={placeholder}
                className="w-full border border-gray-200 bg-gray-50 rounded-lg px-3 py-2 text-sm text-gray-400 cursor-not-allowed"
              />
            </div>
          ))}
        </div>

        <div className="flex gap-2 mt-4">
          <button disabled className="bg-blue-100 text-blue-300 cursor-not-allowed text-sm font-medium px-4 py-2 rounded-lg">
            Salvar (em breve)
          </button>
          <button disabled className="bg-gray-100 text-gray-300 cursor-not-allowed text-sm font-medium px-4 py-2 rounded-lg">
            Testar conexão
          </button>
        </div>
      </div>
    </AdminLayout>
  );
}
