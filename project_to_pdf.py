#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import os

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

ROOT = Path(".").resolve()
OUTPUT = ROOT / "project_dump.pdf"

INCLUDE_EXTS = {
    ".py", ".txt", ".md", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".sh"
}
EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "__pycache__", ".idea",
    ".vscode", "node_modules", "dist", "build"
}
EXCLUDE_FILES = {OUTPUT.name}

PAGE_W, PAGE_H = A4
LEFT = 15 * mm
RIGHT = 15 * mm
TOP = 15 * mm
BOTTOM = 15 * mm

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
]
FONT_NAME = "DejaVuMono"
FONT_SIZE = 9
LINE_STEP = 11  # points


def register_font():
    for path in FONT_PATHS:
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(FONT_NAME, path))
            return
    raise RuntimeError("Не найден TTF-шрифт с поддержкой кириллицы")


def should_skip(path: Path) -> bool:
    if path.name in EXCLUDE_FILES:
        return True
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    return False


def iter_files(root: Path):
    for p in sorted(root.rglob("*")):
        if p.is_file() and not should_skip(p):
            if p.suffix.lower() in INCLUDE_EXTS or p.name == ".gitignore":
                yield p


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp1251", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return f"<ERROR READING FILE: {e}>"
    return "<BINARY OR UNREADABLE CONTENT>"


def wrap_text_line(line: str, max_width: float):
    line = line.replace("\t", "    ")
    if line == "":
        return [""]

    parts = []
    current = ""

    for ch in line:
        test = current + ch
        width = pdfmetrics.stringWidth(test, FONT_NAME, FONT_SIZE)
        if width <= max_width:
            current = test
        else:
            if current:
                parts.append(current)
            current = ch

    if current:
        parts.append(current)

    return parts if parts else [""]


class PdfWriter:
    def __init__(self, out_path: Path):
        self.c = canvas.Canvas(str(out_path), pagesize=A4)
        self.page_num = 1
        self.text = None
        self.start_page()

    def start_page(self):
        self.c.setFont(FONT_NAME, FONT_SIZE)
        self.text = self.c.beginText()
        self.text.setTextOrigin(LEFT, PAGE_H - TOP)
        self.text.setFont(FONT_NAME, FONT_SIZE)
        self.text.setLeading(LINE_STEP)

    def finish_page(self):
        self.c.drawText(self.text)
        self.c.setFont(FONT_NAME, 8)
        self.c.drawRightString(PAGE_W - RIGHT, 8 * mm, f"Стр. {self.page_num}")
        self.c.showPage()
        self.page_num += 1

    def ensure_space(self):
        if self.text.getY() <= BOTTOM:
            self.finish_page()
            self.start_page()

    def write_line(self, line=""):
        self.ensure_space()
        self.text.textLine(line)

    def write_block(self, lines):
        for line in lines:
            self.write_line(line)

    def save(self):
        self.c.drawText(self.text)
        self.c.setFont(FONT_NAME, 8)
        self.c.drawRightString(PAGE_W - RIGHT, 8 * mm, f"Стр. {self.page_num}")
        self.c.save()


def main():
    register_font()
    writer = PdfWriter(OUTPUT)

    max_width = PAGE_W - LEFT - RIGHT
    files = list(iter_files(ROOT))

    writer.write_line(f"Проект: {ROOT.name}")
    writer.write_line(f"Путь: {ROOT}")
    writer.write_line(f"Файлов: {len(files)}")
    writer.write_line("")

    for path in files:
        rel = path.relative_to(ROOT)
        content = read_text(path)

        writer.write_line("=" * 80)
        for part in wrap_text_line(f"FILE: {rel}", max_width):
            writer.write_line(part)
        writer.write_line("=" * 80)
        writer.write_line("")

        for raw in content.splitlines():
            wrapped = wrap_text_line(raw, max_width)
            for part in wrapped:
                writer.write_line(part)

        writer.write_line("")
        writer.write_line("")

    writer.save()
    print(f"Сохранено: {OUTPUT}")


if __name__ == "__main__":
    main()
