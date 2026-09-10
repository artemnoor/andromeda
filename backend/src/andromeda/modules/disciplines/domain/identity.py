from __future__ import annotations

import unicodedata
from hashlib import sha256

from ....shared.contracts.ids import DisciplineId, ShortText


def normalize_discipline_name(source_name: str) -> ShortText:
    """Apply only lossless whitespace/case normalization.

    Punctuation, abbreviations and parenthetical qualifiers are deliberately
    kept, so visually similar but semantically uncertain subjects are not
    merged automatically.
    """

    normalized = " ".join(unicodedata.normalize("NFKC", source_name.replace("\xa0", " ")).casefold().split())
    if not normalized:
        raise ValueError("discipline source name must be non-empty")
    return normalized


def discipline_id_for(normalized_name: str) -> DisciplineId:
    return f"discipline:{sha256(normalized_name.encode('utf-8')).hexdigest()[:16]}"
