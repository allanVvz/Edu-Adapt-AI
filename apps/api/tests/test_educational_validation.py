from app.services.educational_validation_service import (
    apply_educational_quality_gate,
    educational_blockers,
)


def test_quality_gate_removes_fraction_false_positive_calculation():
    output = {
        "math_formatting": {
            "blocks": [{
                "type": "division",
                "operands": [1, 2],
                "result": "0 r 1",
            }]
        },
        "validation": {"approved": True},
        "text_adaptations": [{"content": "Toque na METADE da pizza."}],
    }
    activity = {
        "discipline": "Matemática",
        "title": "Fração: a metade da pizza",
        "question": "Cada parte representa quanto da pizza?",
        "expected_answer": "1/2",
    }

    result = apply_educational_quality_gate(output, activity)

    assert "math_formatting" not in result
    checks = result["validation"]["educational_quality"]["checks"]
    assert any(check["code"] == "math_formatting_fraction_false_positive" for check in checks)
    assert educational_blockers(result) == []


def test_quality_gate_normalizes_pizza_half_and_whole_choices():
    output = {
        "interaction_options": [{
            "type": "multiple_choice",
            "items": [{"name": "Minha resposta"}],
            "zones": [{"name": "🍕 Metade"}, {"name": "🍕🍕 Inteira"}],
            "correct_answer": {"correct_zone": "🍕 Metade"},
        }],
        "validation": {"approved": True},
    }
    activity = {
        "discipline": "Matemática",
        "title": "Fração: a metade da pizza",
        "statement": "Uma pizza foi dividida em 2 partes iguais.",
        "expected_answer": "1/2",
    }

    result = apply_educational_quality_gate(output, activity)

    interaction = result["interaction_options"][0]
    assert interaction["zones"] == [{"name": "◐ Metade da pizza"}, {"name": "● Pizza inteira"}]
    assert interaction["correct_answer"]["correct_zone"] == "◐ Metade da pizza"
    checks = result["validation"]["educational_quality"]["checks"]
    assert any(check["code"] == "fraction_pizza_pictogram_normalized" for check in checks)
