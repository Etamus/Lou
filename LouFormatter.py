import re


_GIF_PATTERN = re.compile(r"(GIF:[\w-]+)", re.IGNORECASE)
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.?!…])\s+")
_MAJUSCULE_SPLIT_PATTERN = re.compile(r"(?<=[a-zá-úç0-9,])\s+(?=[A-ZÁ-ÚÇ])")
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
    "aff",
    "afff",
    "hmm",
    "hmmm",
    "hmmmm",
    "humm",
    "hummm",
    "hummmm",
    "oxe",
    "oxi",
    "oba",
    "bah",
}

_DYNAMIC_INTERJECTION_PATTERN = re.compile(r"^([a-zá-úç]{2,8})([!….,]*)\s+(.*)$", re.IGNORECASE)

_SENTENCE_STARTERS = {
    "agora",
    "hoje",
    "entao",
    "então",
    "mas",
    "quando",
    "onde",
    "enquanto",
    "porém",
    "porem",
    "entretanto",
    "depois",
    "ate",
    "até",
    "bom",
    "olha",
}

_HARD_SENTENCE_BREAKERS = {
    "sem",
    "isso",
    "essa",
    "esse",
    "essas",
    "esses",
    "assim",
    "inclusive",
    "entao",
    "então",
    "mas",
    "só",
    "so",
    "tipo",
    "pois",
    "enfim",
    "aliás",
    "bora",
    "partiu",
}

_TITLE_CONNECTORS = {"da", "de", "do", "das", "dos", "vs", "vs.", "x", "feat", "ft", "and", "the", "of", "&"}

_NAME_STOPWORDS = {"pai", "lou", "mateus", "mãe", "mae"}

_SPLIT_PREFERRED_STARTERS = {
    "lembra",
    "queria",
    "quero",
    "vamos",
    "vamo",
    "bora",
    "olha",
    "pensa",
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


def _clean_token_edges(token: str) -> str:
    if not token:
        return ""
    return re.sub(r"^[^0-9A-Za-zÁ-Úá-úçÇ]+|[^0-9A-Za-zÁ-Úá-úçÇ]+$", "", token)


def _match_dynamic_interjection(text: str) -> list[str] | None:
    snippet = text.strip()
    if not snippet:
        return None
    match = _DYNAMIC_INTERJECTION_PATTERN.match(snippet)
    if not match:
        return None
    word, punctuation, tail = match.groups()
    tail = (tail or "").strip()
    if not tail:
        return None
    if not _looks_like_dynamic_interjection(word or ""):
        return None
    head = f"{word}{punctuation or ''}".strip()
    return [head, tail]


def _looks_like_dynamic_interjection(word: str) -> bool:
    if not word:
        return False
    lower = word.lower()
    if lower in _INTERJECTION_SPLITS:
        return True
    if len(lower) <= 6 and re.search(r"(.)\1{2,}", lower):
        return True
    dynamic_prefixes = ("hum", "hmm", "aff", "ah", "oxe", "oxi", "bah", "eita", "opa")
    if any(lower.startswith(prefix) for prefix in dynamic_prefixes):
        return True
    return False


def _extract_title_like_run(tokens: list[str]) -> list[str]:
    run: list[str] = []
    started = False
    for token in tokens:
        cleaned = _clean_token_edges(token)
        if not cleaned:
            continue
        lower = cleaned.lower()
        if cleaned.isdigit():
            run.append(cleaned)
            started = True
            continue
        if lower in _TITLE_CONNECTORS:
            if started:
                run.append(lower)
                continue
            break
        if cleaned[0].isupper():
            run.append(cleaned)
            started = True
            continue
        break
    if run and any(part[0].isupper() or part.isdigit() for part in run):
        return run
    return []


def _should_force_merge_title(previous: str, current: str) -> bool:
    prev = previous.rstrip()
    curr = current.strip()
    if not prev or not curr:
        return False
    curr_tokens = curr.split()
    if not curr_tokens:
        return False
    first = _clean_token_edges(curr_tokens[0]).lower()
    if first and first in _SENTENCE_STARTERS:
        return False
    title_run = _extract_title_like_run(curr_tokens)
    if not title_run:
        return False
    first_word = _clean_token_edges(curr_tokens[0]).lower()
    if first_word in _SPLIT_PREFERRED_STARTERS:
        return False
    if any(part.isdigit() for part in title_run):
        return True
    return len(title_run) >= 2


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
    for index, chunk in enumerate(chunks):
        candidate = chunk
        if merged:
            candidate = _build_title_candidate(chunks, index)
        if merged and _looks_like_dangling_fragment(merged[-1], candidate):
            merged[-1] = f"{merged[-1]} {chunk}".strip()
        else:
            merged.append(chunk)
    return merged


def _build_title_candidate(chunks: list[str], start_index: int) -> str:
    combined: list[str] = []
    title_started = False
    max_window = 3
    for offset in range(start_index, min(len(chunks), start_index + max_window)):
        token = chunks[offset].strip()
        if not token:
            break
        words = token.split()
        if not words:
            break
        first_clean = _clean_token_edges(words[0])
        if not first_clean:
            break
        lower_first = first_clean.lower()
        if lower_first in _SENTENCE_STARTERS and not title_started:
            break
        if first_clean[0].isupper() or first_clean.isdigit():
            combined.append(token)
            title_started = True
            continue
        if title_started and (lower_first in _TITLE_CONNECTORS or first_clean.isdigit()):
            combined.append(token)
            continue
        break
    return " ".join(combined).strip() if combined else chunks[start_index]


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
    if _looks_like_title_stitch(previous, current):
        return True
    return False


def _looks_like_title_stitch(previous: str, current: str) -> bool:
    prev = previous.rstrip()
    curr = current.strip()
    if not prev or not curr:
        return False
    if prev[-1] in ".?!…":
        return False
    prev_words = prev.split()
    if not prev_words:
        return False
    prev_last = _clean_token_edges(prev_words[-1])
    curr_words = curr.split()
    if not prev_last or not curr_words:
        return False
    curr_first = _clean_token_edges(curr_words[0])
    if not curr_first:
        return False
    if prev_last.lower() in _NAME_STOPWORDS or curr_first.lower() in _NAME_STOPWORDS:
        return False
    if not prev_last[0].isupper() or not curr_first[0].isupper():
        return False
    if len(curr_words) == 1:
        return True
    lookahead = curr_words[1:3]
    for token in lookahead:
        cleaned = _clean_token_edges(token)
        if not cleaned:
            continue
        if cleaned[0].islower() or cleaned.lower() in _TITLE_CONNECTORS:
            return True
    return False


def _looks_like_dangling_fragment(previous: str, current: str) -> bool:
    prev = previous.rstrip()
    curr = current.strip()
    if not prev or not curr:
        return False
    if prev[-1] in ".?!…":
        return False
    if _should_force_merge_title(prev, curr):
        return True
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
    if not curr_words:
        return False
    starter_token = curr_words[0].rstrip(",.!?…").lower()
    if starter_token and starter_token in _SPLIT_PREFERRED_STARTERS:
        return False
    if starter_token in _HARD_SENTENCE_BREAKERS:
        return False
    if len(curr_words) <= 3 and curr_words[0][0].isupper():
        return True
    if _looks_like_title_stitch(prev, curr):
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
    normalized = normalized.replace("'", "")
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
    dynamic = _match_dynamic_interjection(text)
    if dynamic:
        return dynamic
    return [text]