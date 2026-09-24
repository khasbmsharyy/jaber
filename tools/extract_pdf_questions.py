"""Extract Arabic linear-algebra questions from a text PDF.

Usage:
  pip install -r requirements.txt
  python tools/extract_pdf_questions.py "تمارين جبر خطي(2).pdf" pdf_questions.json

If the generated count is zero, the PDF is probably scanned images and OCR is required.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

TOPICS = [
    ("منظومة المعادلات الخطية", ["معادلات", "منظومة", "جاوس", "الحذف"]),
    ("المصفوفات والعمليات عليها", ["مصفوف", "رتبة", "صفوف", "أعمدة", "عمليات سطرية"]),
    ("أنواع المصفوفات", ["نوع المصفوفة", "قطرية", "وحدية", "مثلثية", "منقولة"]),
    ("كتابة عناصر المصفوفة", ["aij", "aᵢⱼ", "عناصر المصفوفة", "بحسب الشروط"]),
    ("المصفوفات الأولية", ["مصفوفة أولية", "مصفوفات أولية"]),
    ("المحددات وخواصها", ["محدد", "det", "قيمة المحدد", "خواص المحدد"]),
    ("العوامل المرافقة", ["عامل مرافق", "العوامل المرافقة", "القاصر", "cofactor"]),
    ("المتجهات والضرب العددي", ["متجه", "ضرب قياسي", "ضرب عددي", "زاوية", "طول المتجه"]),
    ("المركبات والضرب الاتجاهي", ["مركبة أفقية", "مركبة عمودية", "ضرب اتجاهي", "cross"]),
    ("المتجهات الواحدية والمتعامدة", ["متجه واحدي", "متجهات واحدية", "متعامدة", "متعامد قياسياً"]),
    ("المستقيمات والمستويات والمسافة", ["مستقيم", "مستوى", "المسافة", "بعد نقطة"]),
    ("فضاءات المتجهات والاستقلال", ["فضاء متجهات", "فضاء المتجهات", "استقلال", "ارتباط"]),
    ("التحويلات الخطية", ["تحويل خطي", "تحويلات خطية"]),
]

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
QUESTION_START = re.compile(
    r"(?m)^\s*(?:س(?:ؤال)?\s*)?([0-9٠-٩۰-۹]+)\s*[\)\].،.\-:：]\s*"
)


def normalize(text: str) -> str:
    text = text.translate(ARABIC_DIGITS)
    text = text.replace("\u0640", "")
    return re.sub(r"\s+", " ", text).strip()


def topic_for(text: str, current: str = "عام") -> str:
    low = text.casefold()
    for name, words in TOPICS:
        if any(word.casefold() in low for word in words):
            return name
    return current


def split_questions(text: str) -> list[str]:
    text = text.replace("\r", "\n")
    matches = list(QUESTION_START.finditer(text))
    if matches:
        result = []
        for i, match in enumerate(matches):
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            body = normalize(text[match.end():end])
            if len(body) >= 4:
                result.append(body)
        return result

    # Fallback for unnumbered questions.
    return [normalize(part) for part in re.split(r"(?<=[؟?])\s+", normalize(text)) if "؟" in part or "?" in part]


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: extract_pdf_questions.py INPUT.pdf OUTPUT.json")
    source, output = map(Path, sys.argv[1:])
    if not source.exists():
        raise SystemExit(f"PDF not found: {source}")

    document = fitz.open(source)
    items = []
    current_topic = "عام"
    for page_number, page in enumerate(document, 1):
        raw = page.get_text("text")
        if not raw.strip():
            continue
        for line in raw.splitlines():
            line = normalize(line)
            if 3 <= len(line) <= 90 and "؟" not in line and "?" not in line:
                detected = topic_for(line)
                if detected != "عام":
                    current_topic = detected
        for question in split_questions(raw):
            items.append({
                "id": len(items) + 1,
                "topic": topic_for(question, current_topic),
                "question": question,
                "page": page_number,
                "solution": "",
            })

    payload = {
        "source": source.name,
        "page_count": len(document),
        "question_count": len(items),
        "topics": sorted({item["topic"] for item in items}),
        "questions": items,
        "warning": "إذا كان question_count=0 فالملف مصور ويحتاج OCR.",
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"pages={len(document)} questions={len(items)} output={output}")
    if not items:
        print("No text questions found. This PDF likely needs OCR.")


if __name__ == "__main__":
    main()
