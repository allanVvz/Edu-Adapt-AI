"""
PDF generation service for ActivityAdaptation.

Architecture (SOLID):
  S — each method renders exactly one section of the document
  O — new profiles: add PDFConfig to pdf_constants; this file never changes
  L — any PDFConfig is a valid substitute for any other
  I — public surface is render(); internal _draw_* are not exported
  D — renderer receives a PDFConfig abstraction, not a concrete profile object

Usage:
    config = get_profile_config("TEA — Não Verbal")
    pdf_bytes = AdaptationPDFRenderer(output_data, title, config).render()
"""
import io
import os
import re
from typing import Any, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .pdf_constants import (
    A4_USABLE_WIDTH,
    FONT,
    FONT_BOLD,
    PAGE_MARGIN_PT,
    PDFConfig,
)


class AdaptationPDFRenderer:
    """
    Renders an ActivityAdaptation's output_data as an A4 PDF byte stream.

    The renderer is profile-agnostic: all visual decisions live in PDFConfig.
    """

    def __init__(
        self,
        output_data: dict,
        activity_title: str,
        config: PDFConfig,
        discipline: Optional[str] = None,
        static_dir: str = "/app/static",
    ) -> None:
        self._data = output_data
        self._title = activity_title
        self._cfg = config
        self._discipline = discipline
        self._static_dir = static_dir
        self._styles = _build_styles(config)

    # ─── Public ───────────────────────────────────────────────────────────────

    def build_story(self) -> list[Any]:
        """Return flowables including teacher script (for admin/review PDF)."""
        story: list[Any] = []
        story.extend(self._draw_header())
        story.extend(self._draw_text_adaptations())
        story.extend(self._draw_instructions())
        story.extend(self._draw_images())
        story.extend(self._draw_interaction())
        story.extend(self._draw_teacher_script())
        return story

    def build_student_story(self) -> list[Any]:
        """Return flowables for student apostila — no teacher script, print-ready."""
        story: list[Any] = []
        story.extend(self._draw_header())
        story.extend(self._draw_text_adaptations())
        story.extend(self._draw_instructions())
        story.extend(self._draw_images_inline())
        story.extend(self._draw_interaction())
        return story

    def render(self) -> bytes:
        """Build and return the PDF as raw bytes (single activity)."""
        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf,
            pagesize=A4,
            leftMargin=PAGE_MARGIN_PT,
            rightMargin=PAGE_MARGIN_PT,
            topMargin=PAGE_MARGIN_PT,
            bottomMargin=PAGE_MARGIN_PT,
            title=self._title,
            author="EduAdapt AI",
        )
        doc.build(self.build_story())
        return buf.getvalue()

    # ─── Section renderers ────────────────────────────────────────────────────

    def _draw_header(self) -> list:
        cfg = self._cfg
        elements: list[Any] = []

        if self._discipline:
            elements.append(Paragraph(
                self._discipline.upper(),
                self._styles["chip"],
            ))
            elements.append(Spacer(1, 3))

        elements.append(Paragraph(self._title, self._styles["title"]))
        elements.append(Paragraph(cfg.profile_label, self._styles["badge"]))
        elements.append(HRFlowable(
            width="100%",
            thickness=2,
            color=cfg.primary_color,
            spaceAfter=14,
        ))
        return elements

    def _draw_text_adaptations(self) -> list:
        """Render the simplified reading/context text for the activity."""
        raw = self._data.get("text_adaptations")
        if not raw:
            return []

        content: Optional[str] = None
        if isinstance(raw, list) and raw:
            first = raw[0]
            if isinstance(first, dict):
                content = first.get("content") or first.get("text") or first.get("simplified")
            else:
                content = str(first)
        elif isinstance(raw, dict):
            content = (
                raw.get("supported") or raw.get("simplified")
                or raw.get("content") or raw.get("text")
                or next(iter(raw.values()), None)
            )
        elif isinstance(raw, str):
            content = raw

        if not content:
            return []

        return [
            Paragraph(content, self._styles["reading_text"]),
            Spacer(1, 14),
        ]

    def _draw_instructions(self) -> list:
        interactions = self._data.get("interaction_options", [])
        text = (
            interactions[0].get("instructions")
            if interactions
            else self._data.get("print_version", {}).get("instructions")
        )
        if not text:
            return []
        return [
            Paragraph(text, self._styles["instruction"]),
            Spacer(1, 12),
        ]

    def _draw_images(self) -> list:
        slots = self._data.get("image_options", [])
        if not slots:
            return []

        elements: list[Any] = [
            Paragraph("ILUSTRAÇÕES:", self._styles["section_label"]),
        ]

        # Two-column grid using Table; each cell is a nested Table
        rows = []
        for i in range(0, len(slots), 2):
            pair = slots[i:i + 2]
            row = [self._make_image_cell(s) for s in pair]
            if len(row) == 1:
                row.append("")   # fill empty right cell
            rows.append(row)

        col_w = A4_USABLE_WIDTH / 2
        img_table = Table(
            rows,
            colWidths=[col_w, col_w],
            style=TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]),
        )
        elements.append(img_table)
        elements.append(Spacer(1, 10))
        return elements

    def _draw_interaction(self) -> list:
        elements: list[Any] = []
        for interaction in self._data.get("interaction_options", []):
            itype = interaction.get("type", "")
            if itype == "multiple_choice":
                elements.extend(self._draw_multiple_choice(interaction))
            elif itype in ("drag_and_drop", "sequencing", "par"):
                elements.extend(self._draw_drag_or_sequence(interaction))
        return elements

    def _draw_multiple_choice(self, interaction: dict) -> list:
        elements: list[Any] = [
            Paragraph("ESCOLHA UMA RESPOSTA:", self._styles["section_label"]),
        ]
        # zones = the answer choices in MC; items[0] = the question subject (not rendered)
        choices = interaction.get("zones", [])
        for idx, zone in enumerate(choices):
            name = _item_name(zone)
            label = chr(65 + idx)  # A, B, C …
            elements.append(Paragraph(
                f"<b>({label})</b>  {name}",
                self._styles["mc_option"],
            ))
            elements.append(Spacer(1, 10))
        elements.append(Spacer(1, 14))
        return elements

    def _draw_drag_or_sequence(self, interaction: dict) -> list:
        cfg = self._cfg
        elements: list[Any] = []
        items = interaction.get("items", [])
        zones = interaction.get("zones", [])
        itype = interaction.get("type", "")

        # Items bar
        if items:
            elements.append(Paragraph("ITENS:", self._styles["section_label"]))
            n_cols = min(len(items), cfg.max_cols_items)
            col_w = A4_USABLE_WIDTH / n_cols
            item_cells = [[Paragraph(_item_name(it), self._styles["dnd_item"])] for it in items]
            # Chunk into rows of n_cols
            rows = [item_cells[i:i + n_cols] for i in range(0, len(item_cells), n_cols)]
            # Pad last row
            if rows and len(rows[-1]) < n_cols:
                rows[-1].extend([[Paragraph("", self._styles["dnd_item"])]] * (n_cols - len(rows[-1])))
            item_table = Table(
                rows,
                colWidths=[col_w] * n_cols,
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#BBBBBB")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DDDDDD")),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                ]),
            )
            elements.append(item_table)
            elements.append(Spacer(1, 10))

        # Drop-zones
        if zones:
            zone_header = (
                "COLOQUE NA SEQUÊNCIA:" if itype == "sequencing"
                else "ONDE CADA UM PERTENCE:"
            )
            elements.append(Paragraph(zone_header, self._styles["section_label"]))
            zone_rows = []
            for zone in zones:
                zname = _item_name(zone)
                zone_rows.append([
                    Paragraph(zname, self._styles["zone_label"]),
                    Paragraph("", self._styles["body"]),
                ])
            zone_table = Table(
                zone_rows,
                colWidths=[160, A4_USABLE_WIDTH - 160],
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 2, cfg.primary_color),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), cfg.answer_space_height / 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), cfg.answer_space_height / 3),
                    ("BACKGROUND", (1, 0), (1, -1), colors.HexColor("#FAFAFA")),
                ]),
            )
            elements.append(zone_table)
            elements.append(Spacer(1, 14))

        return elements

    def _draw_teacher_script(self) -> list:
        """Narration script at the bottom — for the teacher to read aloud to the child."""
        audio_opts = self._data.get("audio_options", [])
        if not audio_opts:
            return []
        script = audio_opts[0].get("script", "")
        if not script:
            return []

        # Strip TTS control markers before printing
        clean = re.sub(r"\[[^\]]+\]", "", script).strip()
        return [
            HRFlowable(
                width="100%",
                thickness=1,
                color=colors.HexColor("#CCCCCC"),
                spaceBefore=16,
                spaceAfter=8,
            ),
            Paragraph("ROTEIRO DO PROFESSOR:", self._styles["section_label"]),
            Paragraph(clean, self._styles["transcript"]),
        ]

    # ─── Helpers ──────────────────────────────────────────────────────────────

    def _draw_images_inline(self) -> list:
        """Images and text side-by-side — for print apostila layout."""
        slots = [s for s in self._data.get("image_options", []) if s.get("is_active", True)]
        if not slots:
            return []

        elements: list[Any] = []
        cfg = self._cfg

        for slot in slots[:2]:
            description = slot.get("description", "")
            illustration_type = slot.get("illustration_type", "generated")
            emoji = slot.get("emoji", "")
            image_url = slot.get("image_url")

            img_element: Any = None
            if illustration_type == "emoji" and emoji:
                img_element = Paragraph(
                    f'<font size="{int(cfg.image_max_size * 0.55)}">{emoji}</font>',
                    ParagraphStyle("emoji_inline", alignment=1, leading=cfg.image_max_size * 0.65),
                )
            elif image_url:
                local = self._url_to_local(image_url)
                if local and os.path.isfile(local):
                    try:
                        s = int(cfg.image_max_size * 0.8)
                        img_element = Image(local, width=s, height=s)
                    except Exception:
                        pass

            if img_element is None:
                box_size = int(cfg.image_max_size * 0.8)
                img_element = Table(
                    [[Paragraph("", self._styles["placeholder"])]],
                    colWidths=[box_size], rowHeights=[box_size],
                    style=TableStyle([
                        ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#CCCCCC")),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F5F5F5")),
                    ]),
                )

            img_col_w = cfg.image_max_size + 10
            text_col_w = A4_USABLE_WIDTH - img_col_w - 8
            caption = Paragraph(description.capitalize(), self._styles["img_caption"])
            row = Table(
                [[img_element, caption]],
                colWidths=[img_col_w, text_col_w],
                style=TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]),
            )
            elements.append(row)
            elements.append(Spacer(1, 6))

        elements.append(Spacer(1, 10))
        return elements

    def _make_image_cell(self, slot: dict) -> Any:
        """Return a nested Table suitable for a single image-grid cell."""
        description = slot.get("description", "")
        image_url = slot.get("image_url")
        illustration_type = slot.get("illustration_type")

        # Prefer real image file
        if image_url and illustration_type != "emoji":
            local = self._url_to_local(image_url)
            if local and os.path.isfile(local):
                try:
                    size = self._cfg.image_max_size
                    cell_rows = [
                        [Image(local, width=size, height=size)],
                        [Paragraph(description, self._styles["img_caption"])],
                    ]
                    return Table(cell_rows, colWidths=[A4_USABLE_WIDTH / 2 - 16])
                except Exception:
                    pass  # fall through to placeholder

        # Empty picture-frame placeholder; description appears only as caption below
        box_style = TableStyle([
            ("BOX", (0, 0), (-1, -1), 1.5, colors.HexColor("#CCCCCC")),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F0F0F0")),
        ])
        box_size = self._cfg.image_max_size
        placeholder = Table(
            [[Paragraph("", self._styles["placeholder"])]],
            colWidths=[box_size],
            rowHeights=[box_size],
            style=box_style,
        )
        return Table(
            [[placeholder], [Paragraph(description, self._styles["img_caption"])]],
            colWidths=[A4_USABLE_WIDTH / 2 - 16],
        )

    def _url_to_local(self, url: str) -> Optional[str]:
        """Map a /static/images/... URL to an absolute path in the container."""
        if not url:
            return None
        relative = url.lstrip("/")
        if relative.startswith("static/"):
            return os.path.join(self._static_dir, relative[len("static/"):])
        return None


def build_combined_pdf(renderers: list["AdaptationPDFRenderer"]) -> bytes:
    """Merge multiple renderers into a single print-ready apostila PDF."""
    if not renderers:
        return b""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=PAGE_MARGIN_PT,
        rightMargin=PAGE_MARGIN_PT,
        topMargin=PAGE_MARGIN_PT,
        bottomMargin=PAGE_MARGIN_PT,
        title="Apostila de Atividades",
        author="EduAdapt AI",
    )
    full_story: list[Any] = []
    for i, renderer in enumerate(renderers):
        if i > 0:
            full_story.append(PageBreak())
        full_story.extend(renderer.build_student_story())
    doc.build(full_story)
    return buf.getvalue()


# ─── Style factory (pure function — no side effects) ─────────────────────────

def _build_styles(cfg: PDFConfig) -> dict[str, ParagraphStyle]:
    """Build all named paragraph styles from a PDFConfig."""
    fs_t = cfg.font_size_title
    fs_i = cfg.font_size_instruction
    fs_b = cfg.font_size_body
    fs_o = cfg.font_size_option
    ls = cfg.line_spacing
    tc = cfg.text_color
    pc = cfg.primary_color

    def make(name: str, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, **kw)

    return {
        "title": make(
            "title",
            fontName=FONT_BOLD,
            fontSize=fs_t,
            textColor=pc,
            leading=fs_t * ls,
            spaceAfter=4,
        ),
        "chip": make(
            "chip",
            fontName=FONT,
            fontSize=9,
            textColor=cfg.accent_color,
            spaceAfter=2,
        ),
        "badge": make(
            "badge",
            fontName=FONT,
            fontSize=9,
            textColor=cfg.muted_color,
            spaceAfter=8,
        ),
        "reading_text": make(
            "reading_text",
            fontName=FONT,
            fontSize=fs_b,
            textColor=tc,
            leading=fs_b * ls,
            spaceAfter=6,
        ),
        "instruction": make(
            "instruction",
            fontName=FONT_BOLD,
            fontSize=fs_i,
            textColor=tc,
            leading=fs_i * ls,
            spaceAfter=8,
        ),
        "section_label": make(
            "section_label",
            fontName=FONT_BOLD,
            fontSize=10,
            textColor=cfg.muted_color,
            spaceAfter=5,
            spaceBefore=10,
        ),
        "mc_option": make(
            "mc_option",
            fontName=FONT,
            fontSize=fs_o,
            textColor=tc,
            leading=fs_o * ls,
            leftIndent=14,
        ),
        "dnd_item": make(
            "dnd_item",
            fontName=FONT_BOLD,
            fontSize=fs_b,
            textColor=tc,
            alignment=1,
        ),
        "zone_label": make(
            "zone_label",
            fontName=FONT_BOLD,
            fontSize=fs_b,
            textColor=pc,
        ),
        "img_caption": make(
            "img_caption",
            fontName=FONT,
            fontSize=max(fs_b - 2, 9),
            textColor=cfg.muted_color,
            alignment=1,
            spaceAfter=4,
        ),
        "placeholder": make(
            "placeholder",
            fontName=FONT,
            fontSize=fs_b - 1,
            textColor=cfg.muted_color,
            alignment=1,
        ),
        "transcript": make(
            "transcript",
            fontName=FONT,
            fontSize=max(fs_b - 1, 10),
            textColor=cfg.muted_color,
            leading=fs_b * 1.4,
        ),
        "body": make(
            "body",
            fontName=FONT,
            fontSize=fs_b,
            textColor=tc,
        ),
    }


# ─── Utility ──────────────────────────────────────────────────────────────────

def _item_name(item: Any) -> str:
    """Extract a display name from an item, whether str or dict."""
    if isinstance(item, dict):
        return item.get("name") or item.get("label") or str(item)
    return str(item)
