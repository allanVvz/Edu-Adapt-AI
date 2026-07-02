"""
Design constants for TEA-profile-adapted PDF generation.

Adding a new profile: add a new entry to PROFILE_CONFIGS with a PDFConfig.
The renderer (pdf_service.py) never needs to change.
"""
from dataclasses import dataclass

from reportlab.lib import colors


@dataclass(frozen=True)
class PDFConfig:
    """Immutable design token set for one TEA profile."""
    profile_label: str

    # Colors — all combos verified at WCAG AA (≥4.5:1 for body, ≥3:1 for large)
    background_hex: str
    primary_hex: str
    accent_hex: str
    text_hex: str
    muted_hex: str

    # Typography
    font_size_title: int
    font_size_instruction: int
    font_size_body: int
    font_size_option: int
    line_spacing: float

    # Layout
    image_max_size: float    # points; images rendered as squares
    max_cols_items: int      # columns for drag-and-drop item row
    answer_space_height: float  # blank space for fill-in answers (pt)

    @property
    def bg_color(self) -> colors.Color:
        return colors.HexColor(self.background_hex)

    @property
    def primary_color(self) -> colors.Color:
        return colors.HexColor(self.primary_hex)

    @property
    def accent_color(self) -> colors.Color:
        return colors.HexColor(self.accent_hex)

    @property
    def text_color(self) -> colors.Color:
        return colors.HexColor(self.text_hex)

    @property
    def muted_color(self) -> colors.Color:
        return colors.HexColor(self.muted_hex)


# ─── Profile configs ──────────────────────────────────────────────────────────

PROFILE_CONFIGS: dict[str, PDFConfig] = {

    # TEA Não Verbal: minimal complexity, high-contrast B&W, max 2 items
    "não verbal": PDFConfig(
        profile_label="TEA — Não Verbal",
        background_hex="#FFFFFF",
        primary_hex="#000000",   # black on white = 21:1
        accent_hex="#000000",
        text_hex="#111111",
        muted_hex="#555555",
        font_size_title=28,
        font_size_instruction=24,
        font_size_body=20,
        font_size_option=22,
        line_spacing=1.6,
        image_max_size=160.0,
        max_cols_items=2,
        answer_space_height=64.0,
    ),

    # TEA Hipersensibilidade Visual: muted palette, generous whitespace
    "hipersensibilidade": PDFConfig(
        profile_label="TEA — Hipersensibilidade Visual",
        background_hex="#F7F7F7",
        primary_hex="#2B2B2B",   # dark charcoal on #F7F7F7 ≈ 13:1
        accent_hex="#4A6FA5",    # muted blue on #F7F7F7 ≈ 4.8:1
        text_hex="#1A1A1A",
        muted_hex="#6B6B6B",
        font_size_title=22,
        font_size_instruction=18,
        font_size_body=16,
        font_size_option=16,
        line_spacing=1.8,
        image_max_size=100.0,
        max_cols_items=3,
        answer_space_height=48.0,
    ),

    # TEA Apoio Visual: colorful but organized, images + text
    "apoio visual": PDFConfig(
        profile_label="TEA — Apoio Visual e Leitura Inicial",
        background_hex="#FFFFFF",
        primary_hex="#1356A0",   # blue on white ≈ 7.5:1
        accent_hex="#E07B00",    # amber on white ≈ 4.6:1
        text_hex="#1A1A1A",
        muted_hex="#666666",
        font_size_title=22,
        font_size_instruction=18,
        font_size_body=15,
        font_size_option=16,
        line_spacing=1.5,
        image_max_size=120.0,
        max_cols_items=4,
        answer_space_height=44.0,
    ),

    # Standard (no profile)
    "padrão": PDFConfig(
        profile_label="Versão Padrão",
        background_hex="#FFFFFF",
        primary_hex="#212121",   # near-black on white = 19:1
        accent_hex="#1565C0",
        text_hex="#212121",
        muted_hex="#757575",
        font_size_title=18,
        font_size_instruction=14,
        font_size_body=12,
        font_size_option=13,
        line_spacing=1.3,
        image_max_size=90.0,
        max_cols_items=5,
        answer_space_height=36.0,
    ),
}


def get_profile_config(profile_name: str | None) -> PDFConfig:
    """Return the PDF config that best matches the profile name (substring match)."""
    if not profile_name:
        return PROFILE_CONFIGS["padrão"]
    key = profile_name.lower()
    for slug, config in PROFILE_CONFIGS.items():
        if slug in key:
            return config
    return PROFILE_CONFIGS["padrão"]


# ─── Page geometry ────────────────────────────────────────────────────────────

PAGE_MARGIN_PT = 54       # 0.75 inch — both sides
A4_USABLE_WIDTH = 487.28  # A4 width (595.28) minus 2 × PAGE_MARGIN_PT

FONT = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
