import re
import unicodedata
from sqlmodel import Session, select
from ..models.icon_symbol import IconSymbol
from .emoji_service import CONCEPT_EMOJI, get_emoji_for_concept


def normalize_term(text: str) -> str:
    if not text:
        return ""
    no_accents = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in no_accents if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def seed_default_icon_symbols(session: Session) -> int:
    created = 0
    for term, symbol in CONCEPT_EMOJI.items():
        normalized = normalize_term(term)
        existing = session.exec(
            select(IconSymbol).where(IconSymbol.normalized_term == normalized)
        ).first()
        if existing:
            if existing.symbol != symbol:
                existing.symbol = symbol
                session.add(existing)
            continue
        session.add(IconSymbol(
            term=term,
            normalized_term=normalized,
            symbol=symbol,
            symbol_type="emoji",
        ))
        created += 1
    session.commit()
    return created


def find_icon_symbol(session: Session | None, text: str) -> dict | None:
    normalized_text = normalize_term(text)
    if not normalized_text:
        return None

    if session is not None:
        symbols = session.exec(
            select(IconSymbol).where(IconSymbol.is_active == True)  # noqa: E712
        ).all()
        symbols = sorted(symbols, key=lambda s: len(s.normalized_term or ""), reverse=True)
        for symbol in symbols:
            candidates = [symbol.normalized_term]
            if symbol.aliases:
                candidates.extend(normalize_term(alias) for alias in symbol.aliases.split(","))
            if any(candidate and candidate in normalized_text for candidate in candidates):
                return {
                    "symbol": symbol.symbol,
                    "symbol_type": symbol.symbol_type,
                    "term": symbol.term,
                    "source": "icon_symbols",
                }

    fallback = get_emoji_for_concept(text)
    if fallback:
        return {
            "symbol": fallback,
            "symbol_type": "emoji",
            "term": text,
            "source": "emoji_service",
        }
    return None


def apply_icon_symbol(slot: dict, symbol: dict) -> None:
    slot["illustration_type"] = symbol["symbol_type"]
    slot["emoji"] = symbol["symbol"]
    slot["symbol"] = symbol["symbol"]
    slot["symbol_term"] = symbol.get("term")
    slot["symbol_source"] = symbol.get("source")
    slot["image_url"] = None
