# ALL_to_MD_desktop

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Powered by MarkItDown](https://img.shields.io/badge/engine-Microsoft%20MarkItDown-0078D4.svg)](https://github.com/microsoft/markitdown)
[![UI: PyQt6](https://img.shields.io/badge/UI-PyQt6-41CD52.svg)](https://pypi.org/project/PyQt6/)

**ALL_to_MD_desktop** — это удобное, стильное и быстрое кроссплатформенное десктопное приложение на базе инструмента [Microsoft MarkItDown](https://github.com/microsoft/markitdown). Позволяет конвертировать практически любые файлы, документы, медиа и веб-ссылки в чистый **Markdown (`.md`)** как по одному, так и в пакетном режиме.

---

## ✨ Возможности

* **📄 Универсальная конвертация в `.md`:**
  * **Документы:** `.pdf`, `.docx`, `.pptx`, `.xlsx`, `.xls`, `.epub`, `.msg` (Outlook)
  * **Данные и код:** `.html`, `.csv`, `.json`, `.xml`, `.txt`, `.zip` (рекурсивная распаковка и парсинг архивов)
  * **Изображения и Аудио:** `.jpg`, `.png`, `.webp`, `.gif` (EXIF + OCR/LLM описание) и `.mp3`, `.wav`, `.m4a` (транскрибация речи)
  * **Веб-ссылки (URL):** Видео YouTube (извлечение субтитров и метаданных), Wikipedia и любые веб-страницы
* **📚 Пакетный режим (Batch Conversion):**
  * Конвертация десятков и сотен файлов или целых папок (с опцией обхода вложенных подпапок).
  * Гибкое сохранение: в выбранную папку через Проводник, рядом с исходными файлами или склейка всех документов в единый `_merged_bundle.md` (идеально для загрузки базы знаний в LLM).
  * Просмотр любого сконвертированного файла из очереди во встроенном редакторе по двойному клику.
* **🌓 Сплит-редактор и живой предпросмотр:**
  * 3 режима работы: `📝 Код (MD)`, `🌓 Разделенный (50/50)` и `👁️ Превью`.
  * Мгновенная статистика: подсчет строк, слов, символов и оценка количества токенов (`~Tokens`).
* **🤖 Интеграция с LLM Vision и Azure Document Intelligence:**
  * Поддержка OpenAI API и локальных моделей (Ollama / LM Studio / OpenRouter) для генерации текстового описания картинок и презентаций.
* **🎨 Темы оформления:**
  * 4 встроенные цветовые темы: **Slate Dark**, **Daylight Clean**, **Nordic Frost** и **Catppuccin Mocha** + быстрая регулировка размера шрифта (`A-` / `A+`).

---

## 🚀 Установка и запуск

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

### 3. Запуск
```bash
python run.py
```
Либо установите пакет в систему и запускайте командой `all-to-md`:
```bash
pip install -e .
all-to-md
```

---

## 📦 Сборка в автономный `.exe` / бинарный файл

Для сборки в один исполняемый файл без консоли через `PyInstaller`:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "ALL_to_MD_desktop" --paths src --collect-all markitdown run.py
```
Готовый файл появится в папке `dist/`.

---

## ⌨️ Горячие клавиши

| Сочетание | Действие |
| :--- | :--- |
| `Ctrl + O` | Открыть файл через стандартный Проводник |
| `Ctrl + S` | Сохранить Markdown файл («Сохранить как…») |
| `Ctrl + Shift + C` | Скопировать готовый Markdown в буфер обмена |
| `Ctrl + =` / `Ctrl + -` | Увеличить / уменьшить шрифт редактора и превью |

---

## 📄 Лицензия

Распространяется под лицензией [MIT](LICENSE).