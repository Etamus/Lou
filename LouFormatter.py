import re


_GIF_PATTERN = re.compile(r"(GIF:[\w-]+)", re.IGNORECASE)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.?!…])\s+")
_MAJUSCULE_SPLIT_PATTERN = re.compile(r"(?<=[a-zá-úç,])\s+(?=[A-ZÁ-ÚÇ])")
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)
_PREPOSITIONS = {"de", "da", "do", "dos", "das", "pra", "pro", "para", "no", "na", "nos", "nas", "em"}
_PROPER_JOINERS = {"the", "los", "las", "san", "santa", "são"}
_ARTICLE_CONNECTORS = {"o", "a", "os", "as", "um", "uma", "uns", "umas"}
_INTERJECTION_SPLITS = {
    "hehe",
    "haha",
    "hihi",
    "eita",
    "opa",
    "ah",
    "ai",
    "uai",
    "ixi",
    "vish",
}


def sanitize_and_split_response(text: str) -> list:
    """Normalizer that mimics the legacy Lou formatter while fixing edge cases."""

    if not text:
        return []

    if "GIF:" in text:
        return _split_gif_segments(text)

    cleaned = _EMOJI_PATTERN.sub("", text)
    cleaned = cleaned.replace("!", "").strip()
    if not cleaned:
        return []

    lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
    rough_chunks: list[str] = []

    for line in lines:
        sentence_chunks = _SENTENCE_SPLIT_PATTERN.split(line)
        for sentence in sentence_chunks:
            sentence = sentence.strip()
            if not sentence:
                continue
            sub_chunks = _MAJUSCULE_SPLIT_PATTERN.split(sentence)
            for chunk in sub_chunks:
                stripped = chunk.strip()
                if not stripped:
                    continue
                if stripped.startswith(",") and rough_chunks:
                    rough_chunks[-1] = f"{rough_chunks[-1]} {stripped.lstrip(', ').strip()}".strip()
                else:
                    rough_chunks.append(stripped)

    repaired = _merge_proper_nouns(rough_chunks)
    repaired = _merge_dangling_fragments(repaired)

    final_chunks: list[str] = []
    for chunk in repaired:
        normalized = _normalize_chunk(chunk)
        if normalized:
            final_chunks.extend(_split_interjection_chunk(normalized))

    return final_chunks


def _split_gif_segments(text: str) -> list[str]:
    segments = _GIF_PATTERN.split(text)
    tokens: list[str] = []
    for segment in segments:
        stripped = (segment or "").strip()
        if not stripped:
            continue
        if stripped.upper().startswith("GIF:"):
            tokens.append(stripped)
        else:
            tokens.extend(sanitize_and_split_response(stripped))
    return tokens


def _merge_proper_nouns(chunks: list[str]) -> list[str]:
    merged: list[str] = []
    for chunk in chunks:
        if merged and _should_merge_with_previous(merged[-1], chunk):
            merged[-1] = f"{merged[-1]} {chunk}".strip()
        else:
            merged.append(chunk)
    return merged


def _merge_dangling_fragments(chunks: list[str]) -> list[str]:
    merged: list[str] = []
    for chunk in chunks:
        if merged and _looks_like_dangling_fragment(merged[-1], chunk):
            merged[-1] = f"{merged[-1]} {chunk}".strip()
        else:
            merged.append(chunk)
    return merged


def _should_merge_with_previous(previous: str, current: str) -> bool:
    current = current.strip()
    previous = previous.rstrip()
    if not previous or not current:
        return False
    if not current[0].isupper():
        return False
    prev_last_word = previous.split()[-1]
    prev_token = prev_last_word.lower()
    curr_first_word = current.split()[0]
    if prev_token in _PREPOSITIONS:
        return True
    if prev_last_word.lower() in _PROPER_JOINERS:
        return True
    return False


def _looks_like_dangling_fragment(previous: str, current: str) -> bool:
    prev = previous.rstrip()
    curr = current.strip()
    if not prev or not curr:
        return False
    if prev[-1] in ".?!…":
        return False
    # Coloned titles like "Detroit: Become" should merge with continuation words
    if ":" in prev:
        head, tail = prev.rsplit(":", 1)
        tail_words = tail.strip().split()
        if tail.strip() and len(tail_words) <= 2:
            first_curr = curr.split()[0]
            if first_curr and first_curr[0].isupper():
                return True
    prev_last = prev.split()[-1]
    if not prev_last:
        return False
    # Se a frase anterior termina com um artigo e a próxima começa em maiúscula, deve unir
    if prev_last.lower() in _ARTICLE_CONNECTORS and curr.split()[0][0].isupper():
        return True
    if not prev_last[0].isupper():
        return False
    curr_words = curr.split()
    if len(curr_words) <= 3 and curr_words[0][0].isupper():
        return True
    first_token = curr_words[0]
    if first_token.endswith(",") and first_token[0].isupper():
        return True
    return False


def _normalize_chunk(text: str) -> str:
    normalized = text.strip()
    if not normalized:
        return ""
    normalized = normalized.replace("...", "…")
    normalized = normalized.replace(".", "")
    normalized = re.sub(r"\s+,", ",", normalized)
    normalized = re.sub(r",\s+", ", ", normalized)
    normalized = re.sub(r"\s{2,}", " ", normalized)
    if normalized and normalized[0].islower():
        normalized = normalized[0].upper() + normalized[1:]
    return normalized


def _split_interjection_chunk(text: str) -> list[str]:
    if not text:
        return []
    lowered = text.lower()
    for token in _INTERJECTION_SPLITS:
        if lowered.startswith(token + " "):
            head, tail = text[: len(token)], text[len(token):].strip()
            if tail:
                return [head.strip(), tail]
    return [text]