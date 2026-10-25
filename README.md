# ALL_to_MD_desktop

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Version: 0.3.0](https://img.shields.io/badge/version-0.3.0-informational.svg)](https://github.com/YOUR_USERNAME/ALL_to_MD_desktop/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Powered by MarkItDown](https://img.shields.io/badge/engine-Microsoft%20MarkItDown-0078D4.svg)](https://github.com/microsoft/markitdown)

**ALL_to_MD_desktop** — кроссплатформенное десктопное приложение на базе [Microsoft MarkItDown](https://github.com/microsoft/markitdown) для быстрой конвертации документов, таблиц, архивов, изображений, аудио и веб-ссылок в чистый формат **Markdown (`.md`)**.

---

## Основные возможности

* **Все форматы MarkItDown из коробки:**
  * **Документы:** `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.xls`, `.epub`, `.msg` (Outlook)
  * **Веб и данные:** `.html`, `.csv`, `.json`, `.xml`, `.txt`, `.zip` (рекурсивная обработка архивов)
  * **Медиа:** Изображения (`.jpg`, `.png`, `.webp`, `.gif` — EXIF + OCR/LLM описание) и аудио (`.mp3`, `.wav`, `.m4a` — транскрибация)
  * **Ссылки (URL):** Видео YouTube (субтитры и метаданные), Wikipedia и любые веб-страницы
* **3 режима просмотра и работы с документом:**
  * **Превью:** чистый отформатированный вид готового документа.
  * **Исходник | Превью:** синхронное сравнение исходного файла (просмотр изображений, исходных таблиц/текста или карточки документа) и результата конвертации.
  * **Редактор (.md):** возможность вручную отредактировать разметку перед сохранением.
* **Пакетная конвертация (Batch Mode):**
  * Обработка сотен файлов или целых папок (с рекурсивным обходом вложенных подпапок).
  * Сохранение в выбранную папку, рядом с исходными файлами или объединение всей пачки в единый файл `_merged_bundle.md`.
  * Быстрое открытие любого сконвертированного файла из таблицы очереди по двойному клику.
* **Точный подсчет токенов (`tiktoken`):**
  * Встроенный расчет количества токенов по алгоритму `o200k_base` (GPT-4o / современные LLM) с фильтрацией технических данных.
* **Интеграция с LLM Vision и Azure Document Intelligence:**
  * Поддержка OpenAI API и локальных моделей (Ollama / LM Studio / OpenRouter) для генерации текстового описания изображений и слайдов презентаций.
* **Строгий инженерный интерфейс и темы оформления:**
  * 4 темы оформления: **Carbon Dark**, **Paper Light**, **Obsidian Mono**, **Nordic Slate** и настройка масштаба шрифта (`A-` / `A+`).

---

## Установка и запуск из исходного кода

### 1. Клонирование репозитория
```bash
git clone [https://github.com/YOUR_USERNAME/ALL_to_MD_desktop.git](https://github.com/YOUR_USERNAME/ALL_to_MD_desktop.git)
cd ALL_to_MD_desktop
```

### 2. Установка зависимостей
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. Запуск приложения
```bash
python run.py
```
Либо установка пакета в систему:
```bash
pip install -e .
all-to-md
```

---

## Сборка в исполняемый файл (`.exe` / Linux / macOS)

Для локальной сборки автономного приложения через `PyInstaller`:

```bash
pip install pyinstaller pillow
pyinstaller --noconfirm --onefile --windowed --name "ALL_to_MD_desktop" --paths src --collect-all markitdown --collect-all tiktoken --icon=assets/icon.ico --add-data "assets:assets" run.py
```
Готовый файл появится в папке `dist/`.

---

## Горячие клавиши

| Сочетание | Действие |
| :--- | :--- |
| `Ctrl + O` | Открыть файл через системный Проводник |
| `Ctrl + S` | Сохранить Markdown файл («Сохранить как…») |
| `Ctrl + Shift + C` | Скопировать готовый Markdown в буфер обмена |
| `Ctrl + =` / `Ctrl + -` | Увеличить / уменьшить шрифт редактора и превью |

---

## Лицензия

Проект распространяется под лицензией [MIT](LICENSE).