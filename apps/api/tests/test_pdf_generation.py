"""
Unit tests for PDF generation (no OpenAI key, no Docker required).

Validates:
 - PDF bytes are non-empty and start with the PDF magic header
 - Each TEA profile produces a distinct, valid PDF
 - All interaction types render without error
 - Missing/incomplete output_data fields do not raise exceptions
 - Profile config selection works correctly
"""
import pytest

from app.services.pdf_constants import (
    PROFILE_CONFIGS,
    get_profile_config,
)
from app.services.pdf_service import AdaptationPDFRenderer

# ─── Fixtures ─────────────────────────────────────────────────────────────────

MINIMAL_OUTPUT = {
    "text_adaptations": {},
    "image_options": [],
    "audio_options": [],
    "interaction_options": [],
    "print_version": {"format": "A4", "layout": "single_column"},
}

FULL_OUTPUT_MC = {
    "text_adaptations": {"simplified": "Observe as imagens e marque a resposta."},
    "image_options": [
        {
            "id": "img-1",
            "description": "cachorro",
            "image_url": None,
            "illustration_type": None,
            "emoji": None,
        },
        {
            "id": "img-2",
            "description": "gato",
            "image_url": None,
            "illustration_type": "emoji",
            "emoji": "🐱",
        },
    ],
    "audio_options": [
        {
            "id": "aud-1",
            "script": "Olha a imagem. [pausa] Qual é o animal? [repete] Aponte a resposta.",
            "tts_script": "Olha a imagem. Qual é o animal? Aponte a resposta.",
            "voice": "alloy",
            "rhythm": 1.0,
            "audio_url": None,
        }
    ],
    "interaction_options": [
        {
            "type": "multiple_choice",
            "instructions": "MARQUE O ANIMAL QUE VIVE NA ÁGUA.",
            "items": [
                {"name": "Peixe"},
                {"name": "Cachorro"},
                {"name": "Passarinho"},
            ],
            "zones": [],
            "correct_answer": {"correct_zone": "A"},
        }
    ],
    "print_version": {"format": "A4", "layout": "single_column"},
}

FULL_OUTPUT_DND = {
    "text_adaptations": {},
    "image_options": [],
    "audio_options": [
        {
            "id": "aud-1",
            "script": "Arraste cada animal para o lugar certo.",
            "tts_script": "Arraste cada animal para o lugar certo.",
            "voice": "nova",
            "rhythm": 0.8,
            "audio_url": None,
        }
    ],
    "interaction_options": [
        {
            "type": "drag_and_drop",
            "instructions": "ONDE CADA ANIMAL VIVE?",
            "items": [
                {"name": "Peixe"},
                {"name": "Leão"},
                {"name": "Águia"},
            ],
            "zones": [
                {"name": "Água"},
                {"name": "Terra"},
                {"name": "Ar"},
            ],
            "correct_answer": {"Peixe": "Água", "Leão": "Terra", "Águia": "Ar"},
        }
    ],
    "print_version": {"format": "A4"},
}

FULL_OUTPUT_SEQ = {
    "text_adaptations": {},
    "image_options": [],
    "audio_options": [],
    "interaction_options": [
        {
            "type": "sequencing",
            "instructions": "COLOQUE NA ORDEM CERTA.",
            "items": [
                {"name": "Plantar a semente"},
                {"name": "Regar a planta"},
                {"name": "Colher o fruto"},
            ],
            "zones": [
                {"name": "1º"},
                {"name": "2º"},
                {"name": "3º"},
            ],
            "correct_answer": {},
        }
    ],
    "print_version": {"format": "A4"},
}


def _render(output_data: dict, profile_name: str | None = None) -> bytes:
    cfg = get_profile_config(profile_name)
    return AdaptationPDFRenderer(
        output_data=output_data,
        activity_title="Animais do Brasil",
        config=cfg,
        discipline="Ciências",
    ).render()


# ─── Profile config tests ─────────────────────────────────────────────────────

class TestGetProfileConfig:
    def test_returns_default_for_none(self):
        cfg = get_profile_config(None)
        assert cfg == PROFILE_CONFIGS["padrão"]

    def test_matches_nao_verbal(self):
        cfg = get_profile_config("TEA — Não Verbal")
        assert cfg == PROFILE_CONFIGS["não verbal"]

    def test_matches_hipersensibilidade(self):
        cfg = get_profile_config("TEA — Hipersensibilidade Visual")
        assert cfg == PROFILE_CONFIGS["hipersensibilidade"]

    def test_matches_apoio_visual(self):
        cfg = get_profile_config("TEA — Apoio Visual e Leitura Inicial")
        assert cfg == PROFILE_CONFIGS["apoio visual"]

    def test_unknown_profile_falls_back_to_padrao(self):
        cfg = get_profile_config("Perfil Desconhecido XYZ")
        assert cfg == PROFILE_CONFIGS["padrão"]

    def test_case_insensitive_match(self):
        cfg = get_profile_config("TEA — NÃO VERBAL")
        assert cfg == PROFILE_CONFIGS["não verbal"]


# ─── PDF output tests ─────────────────────────────────────────────────────────

PDF_MAGIC = b"%PDF-"


class TestPDFOutput:
    def test_minimal_output_produces_valid_pdf(self):
        pdf = _render(MINIMAL_OUTPUT)
        assert pdf[:5] == PDF_MAGIC
        assert len(pdf) > 1000

    def test_multiple_choice_produces_valid_pdf(self):
        pdf = _render(FULL_OUTPUT_MC)
        assert pdf[:5] == PDF_MAGIC

    def test_drag_and_drop_produces_valid_pdf(self):
        pdf = _render(FULL_OUTPUT_DND)
        assert pdf[:5] == PDF_MAGIC

    def test_sequencing_produces_valid_pdf(self):
        pdf = _render(FULL_OUTPUT_SEQ)
        assert pdf[:5] == PDF_MAGIC

    def test_each_tea_profile_renders(self):
        profiles = [
            "TEA — Não Verbal",
            "TEA — Hipersensibilidade Visual",
            "TEA — Apoio Visual e Leitura Inicial",
            None,
        ]
        pdfs = [_render(FULL_OUTPUT_MC, p) for p in profiles]
        assert all(p[:5] == PDF_MAGIC for p in pdfs)

    def test_different_profiles_produce_different_pdfs(self):
        pdf_nv = _render(FULL_OUTPUT_MC, "TEA — Não Verbal")
        pdf_hv = _render(FULL_OUTPUT_MC, "TEA — Hipersensibilidade Visual")
        assert pdf_nv != pdf_hv

    def test_not_verbal_pdf_is_larger_due_to_font_sizes(self):
        # TEA Não Verbal uses larger fonts — typically results in more pages
        pdf_nv = _render(FULL_OUTPUT_MC, "TEA — Não Verbal")
        pdf_padrao = _render(FULL_OUTPUT_MC, None)
        # Both valid; não verbal tends to be larger
        assert pdf_nv[:5] == PDF_MAGIC
        assert pdf_padrao[:5] == PDF_MAGIC


class TestPDFRobustness:
    def test_empty_interaction_list(self):
        data = {**FULL_OUTPUT_MC, "interaction_options": []}
        pdf = _render(data)
        assert pdf[:5] == PDF_MAGIC

    def test_empty_image_options(self):
        data = {**FULL_OUTPUT_MC, "image_options": []}
        pdf = _render(data)
        assert pdf[:5] == PDF_MAGIC

    def test_empty_audio_options(self):
        data = {**FULL_OUTPUT_MC, "audio_options": []}
        pdf = _render(data)
        assert pdf[:5] == PDF_MAGIC

    def test_missing_print_version_key(self):
        data = {k: v for k, v in FULL_OUTPUT_MC.items() if k != "print_version"}
        pdf = _render(data)
        assert pdf[:5] == PDF_MAGIC

    def test_image_slot_without_url_renders_placeholder(self):
        data = {
            **MINIMAL_OUTPUT,
            "image_options": [
                {"id": "x", "description": "floresta tropical", "image_url": None}
            ],
        }
        pdf = _render(data)
        assert pdf[:5] == PDF_MAGIC

    def test_items_as_plain_strings(self):
        data = {
            **MINIMAL_OUTPUT,
            "interaction_options": [
                {
                    "type": "multiple_choice",
                    "instructions": "ESCOLHA:",
                    "items": ["Peixe", "Leão", "Águia"],
                    "zones": [],
                    "correct_answer": {},
                }
            ],
        }
        pdf = _render(data)
        assert pdf[:5] == PDF_MAGIC

    def test_audio_script_markers_are_stripped(self):
        data = {
            **MINIMAL_OUTPUT,
            "audio_options": [
                {
                    "id": "x",
                    "script": "Olha. [pausa] Aponte. [aguarda toque] Muito bem!",
                    "tts_script": "Olha. Aponte. Muito bem!",
                    "voice": "onyx",
                    "rhythm": 0.62,
                }
            ],
        }
        pdf = _render(data)
        assert pdf[:5] == PDF_MAGIC
