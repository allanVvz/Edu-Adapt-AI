from app.services.math_formatting_service import enhance_math_output_data
from app.services.pdf_constants import get_profile_config
from app.services.pdf_service import AdaptationPDFRenderer


def test_adds_vertical_addition_for_math_activity():
    output = {
        "text_adaptations": [{"version": 1, "content": "54 carrinhos mais 35 carrinhos. Quanto da?"}],
        "interaction_options": [],
    }
    activity = {
        "discipline": "Matemática",
        "title": "Problema de soma",
        "question": "Ronaldo tinha 54 carrinhos e ganhou 35.",
        "expected_answer": "89",
    }

    result = enhance_math_output_data(output, activity)

    block = result["math_formatting"]["blocks"][0]
    assert block["type"] == "addition"
    assert block["symbol"] == "+"
    assert block["operands"] == [54, 35]
    assert block["result"] == "89"
    assert block["rows"][1]["operator"] == "+"


def test_supports_subtraction_multiplication_and_division():
    cases = [
        ("66 - 10", "subtraction", "56", "-"),
        ("12 x 8", "multiplication", "96", "x"),
        ("24 dividido por 6", "division", "4", "÷"),
    ]

    for expression, operation_type, expected_result, symbol in cases:
        result = enhance_math_output_data(
            {"text_adaptations": [{"version": 1, "content": expression}]},
            {"discipline": "Matemática", "question": expression},
        )
        block = result["math_formatting"]["blocks"][0]
        assert block["type"] == operation_type
        assert block["result"] == expected_result
        assert block["symbol"] == symbol


def test_pdf_renderer_accepts_math_formatting_block():
    output = enhance_math_output_data(
        {
            "text_adaptations": [{"version": 1, "content": "Quanto e 33 + 15?"}],
            "interaction_options": [],
            "image_options": [],
        },
        {"discipline": "Matemática", "question": "Quanto e 33 + 15?"},
    )

    pdf = AdaptationPDFRenderer(
        output_data=output,
        activity_title="Soma",
        config=get_profile_config(None),
        discipline="Matemática",
    ).render()

    assert pdf[:5] == b"%PDF-"
    assert len(pdf) > 1000
