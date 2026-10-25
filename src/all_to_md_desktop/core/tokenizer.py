import re

_ENCODING = None
_TIKTOKEN_AVAILABLE = False

try:
    import tiktoken

    _ENCODING = tiktoken.get_encoding("o200k_base")
    _TIKTOKEN_AVAILABLE = True
except Exception:
    _TIKTOKEN_AVAILABLE = False

# Регулярное выражение для исключения гигантских base64-строк при подсчете текстовых токенов
_BASE64_DATA_RE = re.compile(r"data:image/[a-zA-Z]+;base64,[A-Za-z0-9+/=]+")


def count_tokens(text: str) -> tuple[int, bool]:
    """
    Возвращает кортеж (количество_токенов, точный_ли_подсчет).
    Использует BPE-токенизатор o200k_base (GPT-4o / современные LLM).
    """
    if not text:
        return 0, _TIKTOKEN_AVAILABLE

    # Убираем base64-картинки, которые не являются текстовыми токенами
    cleaned = _BASE64_DATA_RE.sub("[IMAGE]", text)

    if _TIKTOKEN_AVAILABLE and _ENCODING is not None:
        try:
            return len(_ENCODING.encode(cleaned, disallowed_special=())), True
        except Exception:
            pass

    # Умный fallback, если tiktoken не установлен:
    # Схлопываем повторяющиеся пробелы и рамки таблиц Markdown (|---|---|),
    # которые в реальных токенизаторах объединяются в одиночные токены.
    compact = re.sub(r"[ \t]{2,}", " ", cleaned)
    compact = re.sub(r"[-=_]{3,}", "---", compact)
    words = re.findall(r"\w+|[^\w\s]", compact, re.UNICODE)
    return int(len(words) * 1.25), False