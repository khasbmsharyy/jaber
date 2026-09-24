"""Extract Arabic linear-algebra questions from the repository PDF.

Usage:
  pip install -r requirements.txt
  python tools/extract_pdf_questions.py "تمارين جبر خطي(2).pdf" pdf_questions.json

The output is intentionally simple so it can be consumed by the browser page.
Headings are used as topics; pages without headings are assigned using keywords.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

TOPICS = [
    ("المعادلات الخطية", ["معادلات", "منظومة", "جاوس", "الحذف"]),
    ("المصفوفات", ["مصفوف", "رتبة", "صفوف", "أعمدة"]),
    ("المحددات والمعكوس", ["محدد", "det", "معكوس", "مرافق"]),
    ("المتجهات", ["متجه", "ضرب قياسي", "ضرب اتجاهي", "زاوية"]),
    ("الفضاءات والمتعة الخطية", ["فضاء", "استقلال", "ارتباط", "تحويل خطي"]),
    ("المستقيمات والمستويات", ["مستقيم", "مستوى", "المسافة", "نقطة"]),
]

QUESTION_RE = re.compile(r"(?m)(?:^|\n)\s*(?:سؤال\s*)?(\d+)[\)\.\-:]\s*(.+?)(?=\n\s*(?:سؤال\s*)?\d+[\)\.\-:]|\Z)", re.S)
HEADING_RE = re.compile(r"(?m)^\s{0,4}([^\n]{2,80})\s*$")

def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def topic_for(text: str, current: str = "عام") -> str:
    low = text.lower()
    for name, words in TOPICS:
        if any(word.lower() in low for word in words):
            return name
    return current

def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_pdf_questions.py INPUT.pdf OUTPUT.json")
    source, output = map(Path, sys.argv[1:])
    doc = fitz.open(source)
    items = []
    current = "عام"
    for page_no, page in enumerate(doc, 1):
        text = page.get_text("text")
        # Prefer short, title-like lines as the current section heading.
        for line in text.splitlines():
            line = clean(line)
            if 3 <= len(line) <= 80 and not re.search(r"[؟?]$", line):
                candidate = topic_for(line)
                if candidate != "عام":
                    current = candidate
        matches = list(QUESTION_RE.finditer(text))
        if not matches:
            # Some PDFs use a question mark without numbering.
            chunks = re.split(r"(?<=[؟?])\s+", clean(text))
            matches = [None] if any("؟" in c or "?" in c for c in chunks) else []
            if matches:
                for chunk in chunks:
                    if "؟" in chunk or "?" in chunk:
                        items.append({"topic": topic_for(chunk, current), "question": chunk, "page": page_no, "solution": ""})
                continue
        for match in matches:
            question = clean(match.group(2))
            items.append({"topic": topic_for(question, current), "question": question, "page": page_no, "solution": ""})
    payload = {"source": source.name, "topics": sorted({x["topic"] for x in items}), "questions": items}
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(items)} questions into {output}")

if __name__ == "__main__":
    main()
