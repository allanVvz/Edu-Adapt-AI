"use client";
import { useEffect, useRef, useState } from "react";
import AdminLayout from "@/components/layout/AdminLayout";
import api from "@/lib/api";
import toast from "react-hot-toast";
import {
  Upload, Trash2, Search, ImageIcon, X, Pencil, Check,
  BookOpen, Loader2,
} from "lucide-react";

interface GalleryItem {
  id: string;
  image_url: string;
  description: string;
  source: string;
  style: string | null;
  prompt: string | null;
  activity_id: string | null;
  created_at: string;
}

const STYLE_LABELS: Record<string, string> = {
  line_art: "Desenho P&B",
  cartoon_2d: "Cartoon",
};

export default function GalleryPage() {
  const [images, setImages] = useState<GalleryItem[]>([]);
  const [search, setSearch] = useState("");
  const [styleFilter, setStyleFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [loading, setLoading] = useState(true);

  // Upload state
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadDesc, setUploadDesc] = useState("");
  const [uploading, setUploading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  // Inline edit description
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingDesc, setEditingDesc] = useState("");
  const [savingDesc, setSavingDesc] = useState(false);

  // Lightbox
  const [lightbox, setLightbox] = useState<GalleryItem | null>(null);

  useEffect(() => { load(); }, []);

  async function load() {
    setLoading(true);
    try {
      const { data } = await api.get("/gallery");
      setImages(data);
    } catch {
      toast.error("Erro ao carregar galeria.");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!uploadFile) { toast.error("Selecione uma imagem."); return; }
    if (!uploadDesc.trim()) { toast.error("Informe uma descrição."); return; }
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", uploadFile);
      form.append("description", uploadDesc.trim());
      await api.post("/gallery/upload", form, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success("Imagem importada com sucesso!");
      setUploadOpen(false);
      setUploadFile(null);
      setUploadDesc("");
      setPreviewUrl(null);
      load();
    } catch {
      toast.error("Erro ao importar imagem.");
    } finally {
      setUploading(false);
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadFile(file);
    setPreviewUrl(URL.createObjectURL(file));
  }

  async function handleDelete(id: string) {
    if (!confirm("Remover imagem da galeria?")) return;
    try {
      await api.delete(`/gallery/${id}`);
      toast.success("Imagem removida.");
      setImages((imgs) => imgs.filter((i) => i.id !== id));
      if (lightbox?.id === id) setLightbox(null);
    } catch {
      toast.error("Erro ao remover.");
    }
  }

  async function saveDescription(id: string) {
    setSavingDesc(true);
    try {
      await api.put(`/gallery/${id}`, { description: editingDesc.trim() });
      setImages((imgs) => imgs.map((i) => i.id === id ? { ...i, description: editingDesc.trim() } : i));
      if (lightbox?.id === id) setLightbox((lb) => lb ? { ...lb, description: editingDesc.trim() } : lb);
      setEditingId(null);
    } catch {
      toast.error("Erro ao salvar descrição.");
    } finally {
      setSavingDesc(false);
    }
  }

  const filtered = images.filter((img) => {
    const matchSearch = !search
      || img.description.toLowerCase().includes(search.toLowerCase())
      || (img.prompt || "").toLowerCase().includes(search.toLowerCase());
    const matchStyle = !styleFilter || img.style === styleFilter;
    const matchSource = !sourceFilter || img.source === sourceFilter;
    return matchSearch && matchStyle && matchSource;
  });

  return (
    <AdminLayout>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Galeria de Imagens</h1>
          <p className="text-sm text-gray-500 mt-0.5">{images.length} imagem(ns) no banco</p>
        </div>
        <button
          onClick={() => setUploadOpen(true)}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-xl"
        >
          <Upload size={15} /> Importar imagem
        </button>
      </div>

      {/* Upload panel */}
      {uploadOpen && (
        <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 mb-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-blue-900">Importar imagem</h3>
            <button onClick={() => { setUploadOpen(false); setUploadFile(null); setPreviewUrl(null); setUploadDesc(""); }}>
              <X size={16} className="text-blue-400 hover:text-blue-700" />
            </button>
          </div>
          <form onSubmit={handleUpload} className="flex gap-5 items-start">
            {/* Preview */}
            <div
              onClick={() => fileRef.current?.click()}
              className="w-36 h-36 flex-shrink-0 rounded-xl border-2 border-dashed border-blue-300 flex items-center justify-center cursor-pointer hover:border-blue-500 overflow-hidden bg-white"
            >
              {previewUrl
                ? <img src={previewUrl} alt="preview" className="w-full h-full object-cover" />
                : <div className="text-center text-blue-400">
                    <ImageIcon size={24} className="mx-auto mb-1" />
                    <p className="text-xs">Clique para selecionar</p>
                  </div>
              }
            </div>
            <input ref={fileRef} type="file" accept="image/*" className="hidden" onChange={handleFileChange} />

            <div className="flex-1 space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">Descrição *</label>
                <input
                  value={uploadDesc}
                  onChange={(e) => setUploadDesc(e.target.value)}
                  placeholder="Ex: Peixe dourado visto de cima, ilustração educacional"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-200"
                />
                <p className="text-xs text-gray-400 mt-1">
                  A descrição é usada para busca e reutilização em outras atividades.
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg"
                >
                  {uploading ? <Loader2 size={14} className="animate-spin" /> : <Upload size={14} />}
                  {uploading ? "Importando..." : "Importar"}
                </button>
                <button
                  type="button"
                  onClick={() => { setUploadOpen(false); setUploadFile(null); setPreviewUrl(null); setUploadDesc(""); }}
                  className="text-sm text-gray-500 px-4 py-2 border border-gray-200 rounded-lg"
                >
                  Cancelar
                </button>
              </div>
            </div>
          </form>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 mb-5 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Buscar por descrição ou prompt..."
            className="w-full pl-9 pr-3 py-2 text-sm border border-gray-200 rounded-xl bg-white focus:outline-none focus:ring-2 focus:ring-blue-200"
          />
        </div>
        <select
          value={styleFilter}
          onChange={(e) => setStyleFilter(e.target.value)}
          className="text-sm border border-gray-200 rounded-xl px-3 py-2 bg-white"
        >
          <option value="">Todos os estilos</option>
          <option value="cartoon_2d">Cartoon colorido</option>
          <option value="line_art">Desenho P&B</option>
        </select>
        <select
          value={sourceFilter}
          onChange={(e) => setSourceFilter(e.target.value)}
          className="text-sm border border-gray-200 rounded-xl px-3 py-2 bg-white"
        >
          <option value="">Todas as origens</option>
          <option value="generated">Geradas por IA</option>
          <option value="uploaded">Importadas</option>
        </select>
        {(search || styleFilter || sourceFilter) && (
          <button
            onClick={() => { setSearch(""); setStyleFilter(""); setSourceFilter(""); }}
            className="text-sm text-gray-500 hover:text-gray-700 px-3 py-2 border border-gray-200 rounded-xl bg-white"
          >
            Limpar filtros
          </button>
        )}
      </div>

      {/* Grid */}
      {loading ? (
        <div className="flex justify-center py-20">
          <div className="animate-spin h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="text-center py-20 text-gray-400">
          <ImageIcon size={40} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">
            {images.length === 0
              ? "Nenhuma imagem na galeria. Gere imagens em uma adaptação ou importe usando o botão acima."
              : "Nenhuma imagem encontrada."}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {filtered.map((img) => (
            <div key={img.id} className="group bg-white rounded-xl border border-gray-200 overflow-hidden hover:border-blue-300 hover:shadow-md transition-all">
              {/* Thumbnail */}
              <div
                className="aspect-square bg-gray-50 cursor-pointer relative"
                onClick={() => setLightbox(img)}
              >
                <img src={img.image_url} alt={img.description} className="w-full h-full object-cover" />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors" />
              </div>

              {/* Info */}
              <div className="p-2.5">
                {editingId === img.id ? (
                  <div className="flex gap-1">
                    <input
                      value={editingDesc}
                      onChange={(e) => setEditingDesc(e.target.value)}
                      className="flex-1 text-xs border border-blue-300 rounded px-1.5 py-1 focus:outline-none"
                      autoFocus
                      onKeyDown={(e) => { if (e.key === "Enter") saveDescription(img.id); if (e.key === "Escape") setEditingId(null); }}
                    />
                    <button onClick={() => saveDescription(img.id)} disabled={savingDesc} className="text-green-600 hover:text-green-800">
                      {savingDesc ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
                    </button>
                    <button onClick={() => setEditingId(null)} className="text-gray-400 hover:text-gray-600">
                      <X size={12} />
                    </button>
                  </div>
                ) : (
                  <p
                    className="text-xs font-medium text-gray-700 line-clamp-2 leading-snug cursor-pointer hover:text-blue-600"
                    onClick={() => { setEditingId(img.id); setEditingDesc(img.description); }}
                    title="Clique para editar"
                  >
                    {img.description}
                  </p>
                )}

                <div className="flex items-center justify-between mt-2">
                  <div className="flex items-center gap-1.5">
                    {img.style && (
                      <span className="text-xs bg-gray-100 text-gray-500 rounded-full px-1.5 py-0.5">
                        {STYLE_LABELS[img.style] ?? img.style}
                      </span>
                    )}
                    {img.source === "uploaded" && (
                      <span className="text-xs bg-purple-50 text-purple-500 rounded-full px-1.5 py-0.5">import</span>
                    )}
                    {img.activity_id && (
                      <span title="Vinculada a uma atividade">
                        <BookOpen size={10} className="text-blue-300" />
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={() => { setEditingId(img.id); setEditingDesc(img.description); }}
                      className="p-1 text-gray-400 hover:text-blue-600 rounded"
                      title="Editar descrição"
                    >
                      <Pencil size={11} />
                    </button>
                    <button
                      onClick={() => handleDelete(img.id)}
                      className="p-1 text-gray-400 hover:text-red-500 rounded"
                      title="Remover"
                    >
                      <Trash2 size={11} />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Lightbox */}
      {lightbox && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" onClick={() => setLightbox(null)}>
          <div className="absolute inset-0 bg-black/70" />
          <div
            className="relative bg-white rounded-2xl shadow-2xl max-w-xl w-full mx-4 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <img src={lightbox.image_url} alt={lightbox.description} className="w-full max-h-[60vh] object-contain bg-gray-50" />
            <div className="p-4">
              {editingId === lightbox.id ? (
                <div className="flex gap-2 mb-2">
                  <input
                    value={editingDesc}
                    onChange={(e) => setEditingDesc(e.target.value)}
                    className="flex-1 border border-blue-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none"
                    autoFocus
                  />
                  <button onClick={() => saveDescription(lightbox.id)} className="text-green-600 hover:text-green-800 px-2">
                    {savingDesc ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
                  </button>
                  <button onClick={() => setEditingId(null)} className="text-gray-400">
                    <X size={14} />
                  </button>
                </div>
              ) : (
                <div className="flex items-start gap-2 mb-2">
                  <p className="flex-1 text-sm font-medium text-gray-800">{lightbox.description}</p>
                  <button
                    onClick={() => { setEditingId(lightbox.id); setEditingDesc(lightbox.description); }}
                    className="text-gray-400 hover:text-blue-600"
                  >
                    <Pencil size={13} />
                  </button>
                </div>
              )}
              <div className="flex items-center justify-between">
                <div className="flex gap-2">
                  {lightbox.style && (
                    <span className="text-xs bg-gray-100 text-gray-500 rounded-full px-2 py-0.5">
                      {STYLE_LABELS[lightbox.style] ?? lightbox.style}
                    </span>
                  )}
                  {lightbox.source === "uploaded" && (
                    <span className="text-xs bg-purple-50 text-purple-500 rounded-full px-2 py-0.5">importada</span>
                  )}
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={() => { handleDelete(lightbox.id); setLightbox(null); }}
                    className="flex items-center gap-1 text-xs text-red-400 hover:text-red-600 px-2 py-1 border border-red-200 rounded-lg"
                  >
                    <Trash2 size={12} /> Remover
                  </button>
                  <button onClick={() => setLightbox(null)} className="text-sm text-gray-500 px-3 py-1 border border-gray-200 rounded-lg">
                    Fechar
                  </button>
                </div>
              </div>
              {lightbox.prompt && (
                <p className="text-xs text-gray-400 mt-2 line-clamp-2" title={lightbox.prompt}>
                  Prompt: {lightbox.prompt}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
