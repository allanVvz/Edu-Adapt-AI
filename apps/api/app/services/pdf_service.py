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
from collections import OrderedDict
from typing import Any, Optional
from urllib.parse import urlparse

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

from .emoji_image_service import emoji_to_png
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
        story_data: Optional[dict] = None,
        static_dir: str = "/app/static",
    ) -> None:
        self._data = output_data
        self._title = activity_title
        self._cfg = config
        self._discipline = discipline
        self._story_data = story_data
        self._static_dir = static_dir
        self._styles = _build_styles(config)

    # ─── Public ───────────────────────────────────────────────────────────────

    def story_key(self) -> Optional[str]:
        if not self._story_data:
            return None
        return self._story_data.get("id") or self._story_data.get("title")

    def build_linked_story_section(self) -> list[Any]:
        return self._draw_linked_story()

    def build_unlinked_group_section(self) -> list[Any]:
        return [
            Paragraph("ATIVIDADES SEM CONTO", self._styles["story_label"]),
            Paragraph("Atividades independentes", self._styles["story_title"]),
            HRFlowable(
                width="100%",
                thickness=2,
                color=self._cfg.primary_color,
                spaceBefore=8,
                spaceAfter=14,
            ),
        ]

    def build_story(self, include_linked_story: bool = True) -> list[Any]:
        """Return flowables including teacher script (for admin/review PDF)."""
        story: list[Any] = []
        if include_linked_story:
            story.extend(self._draw_linked_story())
        story.extend(self._draw_header())
        story.extend(self._draw_text_adaptations())
        story.extend(self._draw_instructions())
        story.extend(self._draw_images())
        story.extend(self._draw_interaction())
        story.extend(self._draw_teacher_script())
        return story

    def build_student_story(self, include_linked_story: bool = True) -> list[Any]:
        """Return flowables for student apostila — no teacher script, print-ready."""
        story: list[Any] = []
        if include_linked_story:
            story.extend(self._draw_linked_story())
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

    def _draw_linked_story(self) -> list:
        if not self._story_data:
            return []

        title = self._story_data.get("title") or "Conto"
        content = self._story_data.get("content") or ""
        if not content:
            return []

        elements: list[Any] = [
            Paragraph("BLOCO DE CONTO", self._styles["story_label"]),
            Paragraph(title, self._styles["story_title"]),
            Paragraph("Atividades vinculadas a este conto", self._styles["story_meta"]),
            Paragraph(self._emojify(content), self._styles["story_text"]),
        ]
        elements.extend(self._draw_story_images_inline())
        elements.append(HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#CCCCCC"),
            spaceBefore=10,
            spaceAfter=14,
        ))
        return elements

    def _draw_story_images_inline(self) -> list:
        slots = [
            slot for slot in (self._story_data or {}).get("image_options", [])
            if isinstance(slot, dict) and slot.get("is_active", True)
        ]
        if not slots:
            return []

        rows = []
        for i in range(0, min(len(slots), 4), 2):
            pair = slots[i:i + 2]
            row = [self._make_image_cell(slot) for slot in pair]
            if len(row) == 1:
                row.append(Paragraph("", self._styles["body"]))
            rows.append(row)

        col_w = A4_USABLE_WIDTH / 2
        return [
            Paragraph("PICTOGRAMAS DO CONTO:", self._styles["section_label"]),
            Table(
                rows,
                colWidths=[col_w, col_w],
                style=TableStyle([
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]),
            ),
            Spacer(1, 10),
        ]

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
            Paragraph(self._emojify(_to_analog(content)), self._styles["reading_text"]),
            Spacer(1, 14),
        ]

    def _draw_instructions(self) -> list:
        interactions = self._data.get("interaction_options", [])
        text = (
            interactions[0].get("instructions")
            if interactions
            else self._data.get("print_version", {}).get("instructions")
        )
        text = _to_analog(text)
        if not text:
            return []
        return [
            Paragraph(self._emojify(text, self._cfg.font_size_instruction),
                      self._styles["instruction"]),
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
        cfg = self._cfg
        elements: list[Any] = [
            Paragraph("MARQUE A RESPOSTA CERTA COM UM X:", self._styles["section_label"]),
        ]
        # zones = the answer choices in MC; items[0] = the question subject (not rendered)
        choices = interaction.get("zones", [])
        if not choices:
            elements.append(Spacer(1, 14))
            return elements

        box = cfg.font_size_option + 4  # checkbox side, in points
        glyph_size = cfg.font_size_option + 6

        # Use an emoji column only if at least one option carries a pictogram.
        parsed = [_split_label_emoji(_item_name(z)) for z in choices]
        has_emoji = any(self._emoji_image(e, glyph_size) is not None for e, _ in parsed)

        rows = []
        for emoji, label in parsed:
            checkbox = Table(
                [[""]], colWidths=[box], rowHeights=[box],
                style=TableStyle([
                    ("BOX", (0, 0), (-1, -1), 1.5, cfg.primary_color),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                ]),
            )
            label_para = Paragraph(label, self._styles["mc_option"])
            if has_emoji:
                glyph = self._emoji_image(emoji, glyph_size) or Paragraph("", self._styles["body"])
                rows.append([checkbox, glyph, label_para])
            else:
                rows.append([checkbox, label_para])

        if has_emoji:
            col_widths = [box + 14, glyph_size + 12, A4_USABLE_WIDTH - box - glyph_size - 26]
        else:
            col_widths = [box + 14, A4_USABLE_WIDTH - box - 14]

        table = Table(
            rows, colWidths=col_widths,
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ]),
        )
        elements.append(table)
        elements.append(Spacer(1, 14))
        return elements

    def _draw_drag_or_sequence(self, interaction: dict) -> list:
        cfg = self._cfg
        elements: list[Any] = []
        items = interaction.get("items", [])
        zones = interaction.get("zones", [])
        itype = interaction.get("type", "")

        # ── Items to cut out ──────────────────────────────────────────────────
        # "Drag and drop" on screen becomes "cut and paste" on paper: each item
        # is a card framed by a dashed cut-line, headed by a scissors pictogram.
        if items:
            elements.append(self._cut_header("RECORTE ESTAS FIGURAS:"))
            n_cols = min(len(items), cfg.max_cols_items)
            col_w = A4_USABLE_WIDTH / n_cols
            glyph_size = cfg.font_size_body + 14

            item_cells = [[self._cut_item_flowable(_item_name(it), glyph_size)] for it in items]
            rows = [item_cells[i:i + n_cols] for i in range(0, len(item_cells), n_cols)]
            if rows and len(rows[-1]) < n_cols:
                rows[-1].extend([[Paragraph("", self._styles["dnd_item"])]] * (n_cols - len(rows[-1])))

            item_table = Table(
                rows,
                colWidths=[col_w] * n_cols,
                style=TableStyle([
                    # Dashed border = "cut here" guideline
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#999999"), None, [3, 2]),
                    ("INNERGRID", (0, 0), (-1, -1), 1, colors.HexColor("#999999"), None, [3, 2]),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 12),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FCFCFC")),
                ]),
            )
            elements.append(item_table)
            elements.append(Spacer(1, 12))

        # ── Where to glue them ────────────────────────────────────────────────
        if zones:
            zone_header = (
                "RECORTE E COLE NA ORDEM CERTA:" if itype == "sequencing"
                else "COLE CADA FIGURA NO LUGAR CERTO:"
            )
            elements.append(Paragraph(zone_header, self._styles["section_label"]))
            zone_rows = []
            for zone in zones:
                emoji, zlabel = _split_label_emoji(_item_name(zone))
                glyph = self._emoji_image(emoji, cfg.font_size_body + 6)
                left = (
                    Table([[glyph, Paragraph(zlabel, self._styles["zone_label"])]],
                          colWidths=[cfg.font_size_body + 14, 160 - cfg.font_size_body - 14],
                          style=TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                                            ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
                    if glyph else Paragraph(zlabel, self._styles["zone_label"])
                )
                zone_rows.append([left, Paragraph("cole aqui", self._styles["glue_hint"])])
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

    def _cut_header(self, text: str) -> Any:
        """Section header prefixed with a scissors pictogram."""
        label = Paragraph(text, self._styles["section_label"])
        glyph = self._emoji_image("✂️", 14)
        if glyph is None:
            return label
        return Table(
            [[glyph, label]],
            colWidths=[22, A4_USABLE_WIDTH - 22],
            style=TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
            ]),
        )

    def _cut_item_flowable(self, name: str, glyph_size: float) -> Any:
        """A cut-out card: emoji pictogram stacked above its label."""
        emoji, label = _split_label_emoji(name)
        glyph = self._emoji_image(emoji, glyph_size)
        text = Paragraph(label, self._styles["dnd_item"])
        if glyph is None:
            return text
        return Table(
            [[glyph], [text]],
            style=TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 1),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
            ]),
        )

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
        """Images side-by-side with caption — for student apostila layout."""
        slots = [s for s in self._data.get("image_options", []) if s.get("is_active", True)]
        if not slots:
            return []

        elements: list[Any] = []
        col_w = A4_USABLE_WIDTH / 2 - 8

        pair = slots[:2]
        row_cells = []
        for slot in pair:
            box = self._make_image_cell(slot)
            row_cells.append(box)
        if len(row_cells) == 1:
            row_cells.append(Paragraph("", self._styles["body"]))

        img_table = Table(
            [row_cells],
            colWidths=[col_w, col_w],
            style=TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]),
        )
        elements.append(img_table)
        elements.append(Spacer(1, 10))
        return elements

    def _make_image_cell(self, slot: dict) -> Any:
        """Render one image slot: real image, then emoji pictogram, else label box."""
        description = slot.get("description", "")
        image_url = slot.get("image_url")
        emoji = slot.get("emoji", "")
        illustration_type = slot.get("illustration_type", "generated")
        col_w = A4_USABLE_WIDTH / 2 - 16
        box_size = self._cfg.image_max_size

        caption = Paragraph(description, self._styles["img_caption"])

        # 1) Real generated image file
        if image_url and illustration_type != "emoji":
            local = self._url_to_local(image_url)
            if local and os.path.isfile(local):
                try:
                    img = Image(local, width=box_size, height=box_size)
                    return Table([[img], [caption]], colWidths=[col_w])
                except Exception:
                    pass

        # 2) Emoji pictogram — rasterized to PNG so the glyph is faithfully shown
        if emoji:
            png = emoji_to_png(emoji, size=160, cache_dir=self._emoji_cache_dir())
            if png and os.path.isfile(png):
                try:
                    pad = box_size * 0.12
                    glyph = Image(png, width=box_size - 2 * pad, height=box_size - 2 * pad)
                    framed = Table(
                        [[glyph]],
                        colWidths=[box_size], rowHeights=[box_size],
                        style=TableStyle([
                            ("BOX", (0, 0), (-1, -1), 2, self._cfg.primary_color),
                            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                            ("BACKGROUND", (0, 0), (-1, -1), self._concept_bg()),
                        ]),
                    )
                    return Table([[framed], [caption]], colWidths=[col_w])
                except Exception:
                    pass

        # 3) Concept label box — last-resort fallback (no emoji font / no image)
        concept = Table(
            [[Paragraph(description.upper(), self._styles["concept_label"])]],
            colWidths=[box_size],
            rowHeights=[box_size],
            style=TableStyle([
                ("BOX", (0, 0), (-1, -1), 2.5, self._cfg.primary_color),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("BACKGROUND", (0, 0), (-1, -1), self._concept_bg()),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]),
        )
        return Table([[concept], [caption]], colWidths=[col_w])

    def _emoji_cache_dir(self) -> str:
        return os.path.join(self._static_dir, "emoji")

    def _emoji_image(self, emoji: str, size: float) -> Optional[Any]:
        """Return a square Image flowable for an emoji, or None if unavailable."""
        if not emoji:
            return None
        png = emoji_to_png(emoji, size=max(96, int(size * 2)), cache_dir=self._emoji_cache_dir())
        if png and os.path.isfile(png):
            try:
                return Image(png, width=size, height=size)
            except Exception:
                return None
        return None

    def _emojify(self, text: str, size: Optional[float] = None) -> str:
        """Replace inline emoji in free text with inline <img> tags (faithful glyphs).

        Without this, emoji embedded in a Helvetica Paragraph render as tofu (■).
        Falls back to dropping the emoji when the font/render is unavailable.
        """
        if not text:
            return ""
        sz = size if size is not None else self._cfg.font_size_body

        def repl(m: "re.Match") -> str:
            png = emoji_to_png(m.group(0), size=max(96, int(sz * 2)),
                               cache_dir=self._emoji_cache_dir())
            if png and os.path.isfile(png):
                return f'<img src="{png}" width="{sz:.0f}" height="{sz:.0f}" valign="middle"/> '
            return ""

        return _ANY_EMOJI.sub(repl, text).strip()

    def _concept_bg(self) -> colors.Color:
        """Light tint (15% primary + 85% white) for concept label box background."""
        ph = self._cfg.primary_hex.lstrip("#")
        r, g, b = int(ph[0:2], 16), int(ph[2:4], 16), int(ph[4:6], 16)
        return colors.Color((r * 0.12 + 255 * 0.88) / 255,
                            (g * 0.12 + 255 * 0.88) / 255,
                            (b * 0.12 + 255 * 0.88) / 255)

    def _url_to_local(self, url: str) -> Optional[str]:
        """Map a /static/images/... URL to an absolute path in the container."""
        if not url:
            return None
        path = urlparse(url).path if "://" in url else url
        relative = path.lstrip("/")
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
    first_section = True
    for story_key, group in _group_renderers_by_story(renderers):
        if not first_section:
            full_story.append(PageBreak())
        first_section = False

        if story_key:
            full_story.extend(group[0].build_linked_story_section())
            for renderer in group:
                full_story.append(PageBreak())
                full_story.extend(renderer.build_student_story(include_linked_story=False))
            continue

        full_story.extend(group[0].build_unlinked_group_section())
        for i, renderer in enumerate(group):
            full_story.append(PageBreak())
            full_story.extend(renderer.build_student_story(include_linked_story=False))
    doc.build(full_story)
    return buf.getvalue()


# ─── Style factory (pure function — no side effects) ─────────────────────────

def _group_renderers_by_story(
    renderers: list["AdaptationPDFRenderer"],
) -> list[tuple[Optional[str], list["AdaptationPDFRenderer"]]]:
    story_groups: "OrderedDict[str, list[AdaptationPDFRenderer]]" = OrderedDict()
    unlinked: list[AdaptationPDFRenderer] = []
    for renderer in renderers:
        key = renderer.story_key()
        if key:
            story_groups.setdefault(key, []).append(renderer)
        else:
            unlinked.append(renderer)

    groups: list[tuple[Optional[str], list["AdaptationPDFRenderer"]]] = [
        (key, group) for key, group in story_groups.items()
    ]
    if unlinked:
        groups.append((None, unlinked))
    return groups


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
        "story_label": make(
            "story_label",
            fontName=FONT_BOLD,
            fontSize=10,
            textColor=cfg.accent_color,
            spaceAfter=4,
        ),
        "story_title": make(
            "story_title",
            fontName=FONT_BOLD,
            fontSize=max(fs_t - 2, fs_b + 4),
            textColor=pc,
            leading=max(fs_t - 2, fs_b + 4) * ls,
            spaceAfter=8,
        ),
        "story_meta": make(
            "story_meta",
            fontName=FONT,
            fontSize=max(fs_b - 2, 9),
            textColor=cfg.muted_color,
            spaceAfter=8,
        ),
        "story_text": make(
            "story_text",
            fontName=FONT,
            fontSize=fs_b,
            textColor=tc,
            leading=fs_b * ls,
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
        "concept_label": make(
            "concept_label",
            fontName=FONT_BOLD,
            fontSize=min(fs_b + 4, 22),
            textColor=pc,
            alignment=1,
            leading=min(fs_b + 4, 22) * 1.3,
            wordWrap="LTR",
        ),
        "glue_hint": make(
            "glue_hint",
            fontName=FONT,
            fontSize=max(fs_b - 4, 8),
            textColor=cfg.muted_color,
            alignment=1,
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


# Matches one emoji cluster (base symbol + optional modifiers/ZWJ/VS-16).
_EMOJI_CLUSTER = (
    r"[\U0001F000-\U0001FAFF\U00002600-\U000026FF\U00002700-\U000027BF"
    r"\U00002B00-\U00002BFF\U0001F1E6-\U0001F1FF\U00002190-\U000021FF\U00002B05-\U00002B07]"
    r"[︀-️‍\U0001F3FB-\U0001F3FF]*"
)
_LEADING_EMOJI = re.compile(r"^(?:" + _EMOJI_CLUSTER + r")+")
_ANY_EMOJI = re.compile(_EMOJI_CLUSTER)


def _split_label_emoji(name: str) -> tuple[Optional[str], str]:
    """Split a leading emoji from a label: '🥬 Alface' → ('🥬', 'Alface')."""
    if not name:
        return None, ""
    m = _LEADING_EMOJI.match(name)
    if m:
        emoji = m.group(0).strip()
        rest = name[m.end():].strip()
        return (emoji or None), (rest or name)
    return None, name


# Digital → analog (print) verb map. The printed apostila is worked with pencil,
# scissors and glue, so on-screen verbs must become physical actions.
_ANALOG_REPLACEMENTS: list[tuple[str, str]] = [
    (r"arraste\s+e\s+solte", "recorte e cole"),
    (r"arrastar\s+e\s+soltar", "recortar e colar"),
    (r"arraste", "recorte e cole"),
    (r"arrastar", "recortar e colar"),
    (r"arrasta", "recorta e cola"),
    (r"solte", "cole"),
    (r"soltar", "colar"),
    (r"toque\s+e\s+arraste", "recorte e cole"),
    (r"toque\s+na", "marque a"),
    (r"toque\s+no", "marque o"),
    (r"toque\s+em", "marque"),
    (r"toque", "marque"),
    (r"tocar", "marcar"),
    (r"clique\s+na", "marque a"),
    (r"clique\s+no", "marque o"),
    (r"clique\s+em", "marque"),
    (r"clique", "marque"),
    (r"clicar", "marcar"),
    (r"selecione", "marque"),
    (r"selecionar", "marcar"),
    (r"aperte", "marque"),
    (r"apertar", "marcar"),
    (r"\[aguarda\s+toque\]", ""),
]


def _match_case(original: str, replacement: str) -> str:
    """Apply *replacement* preserving the capitalization pattern of *original*."""
    if original.isupper():
        return replacement.upper()
    if original[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement


def _to_analog(text: Optional[str]) -> str:
    """Rewrite on-screen (digital) verbs into physical print actions."""
    if not text:
        return ""
    out = text
    for pattern, repl in _ANALOG_REPLACEMENTS:
        out = re.sub(
            pattern,
            lambda m, r=repl: _match_case(m.group(0), r),
            out,
            flags=re.IGNORECASE,
        )
    return re.sub(r"\s{2,}", " ", out).strip()
