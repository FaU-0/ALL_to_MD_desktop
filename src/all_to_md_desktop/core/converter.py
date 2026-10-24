try:
    from markitdown import MarkItDown
except ImportError:
    MarkItDown = None


def create_markitdown_instance(config: dict):
    """Создает и настраивает экземпляр MarkItDown с поддержкой плагинов, LLM и Azure."""
    if MarkItDown is None:
        raise RuntimeError(
            "Библиотека 'markitdown' не найдена.\n"
            "Установите её командой: pip install \"markitdown[all]\""
        )

    kwargs = {"enable_plugins": config.get("enable_plugins", False)}

    if config.get("use_llm", False):
        api_key = config.get("llm_api_key", "").strip()
        base_url = config.get("llm_base_url", "").strip() or None
        model = config.get("llm_model", "gpt-4o-mini").strip()

        if not api_key and not base_url:
            raise ValueError(
                "Для использования LLM-описаний укажите API-ключ или локальный Base URL в настройках."
            )

        from openai import OpenAI

        client = OpenAI(api_key=api_key or "local-key", base_url=base_url)
        kwargs["llm_client"] = client
        kwargs["llm_model"] = model

    docintel = config.get("docintel_endpoint", "").strip()
    if docintel:
        kwargs["docintel_endpoint"] = docintel

    return MarkItDown(**kwargs)