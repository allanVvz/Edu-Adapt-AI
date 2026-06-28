"use client";
import { useEffect, useState } from "react";
import { X, Search, ImageIcon, Check } from "lucide-react";
import api from "@/lib/api";

interface GalleryItem {
  id: string;
  image_url: string;
  description: string;
  source: string;
  style: string | null;
  prompt: string | null;
  created_at: string;
}

type ImageStyle = "pictogram" | "line_art" | "cartoon_2d";

const STYLE_LABELS: Record<ImageStyle, string> = {
  pictogram: "Pictograma",
  line_art: "Desenho P&B",
  cartoon_2d: "Cartoon",
};

interface Props {
  open: boolean;
  onClose: () => void;
  onSelect: (imageUrl: string, galleryImageId: string, style: ImageStyle | null) => void;
  currentImageUrl?: string | null;
  initialStyle?: ImageStyle;
}

export default function ImagePickerModal({ open, onClose, onSelect, currentImageUrl, initialStyle = "pictogram" }: Props) {
  const [images, setImages] = useState<GalleryItem[]>([]);
  const [search, setSearch] = useState("");
  const [styleFilter, setStyleFilter] = useState<"" | ImageStyle>(initialStyle);
  const [loading, setLoading] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSearch("");
      setStyleFilter(initialStyle);
      setSelectedId(null);
      load();
    }
  }, [open, initialStyle]);

  async function load() {
    setLoading(true);
    try {
      const { data } = await api.get("/gallery");
      setImages(data);
    } catch {
      /* silent */
    } finally {
      setLoading(false);
    }
  }

  const filtered = images.filter((img) => {
    const matchSearch = !search || img.description.toLowerCase().includes(search.toLowerCase())
      || (img.prompt || "").toLowerCase().includes(search.toLowerCase());
    const matchStyle = !styleFilter || img.style === styleFilter;
    return matchSearch && matchStyle;
  });

  function handleSelect(img: GalleryItem) {
    setSelectedId(img.id);
    onSelect(img.image_url, img.id, img.style as ImageStyle | null);
    onClose();
  }

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[85vh] flex flex-col mx-4">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <div>
            <h2 className="font-bold text-gray-900">Galeria de Imagens</h2>
            <p className="text-xs text-gray-400 mt-0.5">Selecione uma imagem para usar neste slot</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <X size={16} className="text-gray-500" />
          </button>
        </div>

        {/* Filters */}
        <div className="px-5 py-3 border-b border-gray-100 flex gap-3">
          <div className="flex-1 relative">
            <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Buscar por descrição ou prompt..."
              className="w-full pl-8 pr-3 py-1.5 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200"
              autoFocus
            />
          </div>
          <select
            value={styleFilter}
            onChange={(e) => setStyleFilter(e.target.value as "" | ImageStyle)}
            className="text-sm border border-gray-200 rounded-lg px-2 py-1.5"
          >
            <option value="">Todos os estilos</option>
            <option value="pictogram">Pictogramas</option>
            <option value="cartoon_2d">Cartoon colorido</option>
            <option value="line_art">Desenho P&B</option>
          </select>
        </div>

        {/* Grid */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading ? (
            <div className="flex justify-center py-10">
              <div className="animate-spin h-6 w-6 border-4 border-blue-500 border-t-transparent rounded-full" />
            </div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-14 text-gray-400">
              <ImageIcon size={36} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">
                {images.length === 0
                  ? "Nenhuma imagem na galeria. Gere imagens em uma adaptação primeiro."
                  : "Nenhuma imagem encontrada para essa busca."}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
              {filtered.map((img) => {
                const isCurrent = img.image_url === currentImageUrl;
                const isSelected = img.id === selectedId;
                return (
                  <button
                    key={img.id}
                    onClick={() => handleSelect(img)}
                    className={`group relative text-left rounded-xl overflow-hidden border-2 transition-all ${
                      isCurrent
                        ? "border-green-400 ring-2 ring-green-200"
                        : isSelected
                          ? "border-blue-500 ring-2 ring-blue-200"
                          : "border-gray-200 hover:border-blue-300"
                    }`}
                  >
                    <div className="aspect-square bg-gray-50 relative">
                      <img
                        src={img.image_url}
                        alt={img.description}
                        className="w-full h-full object-cover"
                      />
                      {isCurrent && (
                        <div className="absolute top-1.5 right-1.5 bg-green-500 text-white rounded-full p-0.5">
                          <Check size={10} />
                        </div>
                      )}
                    </div>
                    <div className="p-2">
                      <p className="text-xs font-medium text-gray-700 line-clamp-2 leading-snug">
                        {img.description}
                      </p>
                      {img.style && (
                        <p className="text-xs text-gray-400 mt-0.5">
                          {STYLE_LABELS[img.style as ImageStyle] ?? img.style}
                        </p>
                      )}
                      {img.source === "uploaded" && (
                        <span className="text-xs text-purple-500">importada</span>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-5 py-3 border-t border-gray-100 flex items-center justify-between">
          <p className="text-xs text-gray-400">{filtered.length} imagem(ns) disponível(is)</p>
          <button onClick={onClose} className="text-sm text-gray-500 hover:text-gray-700 px-4 py-1.5 border border-gray-200 rounded-lg">
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
