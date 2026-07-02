"""
Apply the deterministic educational quality gate to existing adaptations.

Usage:
    python -m app.scripts.apply_educational_quality_gate
"""
from __future__ import annotations

from sqlmodel import Session, select

from ..database import engine
from ..models.activity import Activity
from ..models.adaptation import ActivityAdaptation
from ..services.educational_validation_service import apply_educational_quality_gate


def _activity_context(activity: Activity | None) -> dict:
    if not activity:
        return {}
    return {
        "title": activity.title,
        "discipline": activity.discipline,
        "statement": activity.statement,
        "question": activity.question,
        "expected_answer": activity.expected_answer,
        "pedagogical_objective": activity.pedagogical_objective,
        "teacher_notes": activity.teacher_notes,
    }


def run() -> None:
    scanned = 0
    updated = 0
    with Session(engine) as session:
        adaptations = session.exec(select(ActivityAdaptation)).all()
        for adaptation in adaptations:
            scanned += 1
            activity = session.get(Activity, adaptation.activity_id)
            current = adaptation.output_data or {}
            checked = apply_educational_quality_gate(current, _activity_context(activity))
            if checked != current:
                adaptation.output_data = checked
                session.add(adaptation)
                updated += 1
        session.commit()
    print(f"[apply_educational_quality_gate] scanned={scanned} updated={updated}")


if __name__ == "__main__":
    run()
