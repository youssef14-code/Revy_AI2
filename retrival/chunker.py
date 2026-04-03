# chunker.py
import re
from typing import List, Dict

SECTION_REGEX = r"\n(\d+)\.\s(.+?)\n"

def split_layers(text: str) -> Dict[str, str]:
    """
    Split document into logical layers.
    """
    tech_marker = "TECHNICAL EXPLANATION LAYER"

    agent_part, tech_part = text.split(tech_marker)

    return {
        "agent_knowledge_base": agent_part.strip(),
        "technical_explanation_layer": tech_marker + tech_part.strip()
    }


def split_sections(layer_text: str) -> List[Dict]:
    """
    Split a layer into numbered sections (1–9).
    Each section is a single chunk.
    """
    matches = list(re.finditer(SECTION_REGEX, layer_text))
    sections = []

    for i, match in enumerate(matches):
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(layer_text)

        sections.append({
            "section_id": int(match.group(1)),
            "section_title": match.group(2).strip(),
            "text": layer_text[start:end].strip()
        })

    return sections


GENERIC_TITLES = {
    "context",
    "overview",
    "description",
    "notes",
    "summary",
    "introduction"
}


def extract_internal_title(text: str) -> str:
    for line in text.split("\n"):
        line = line.strip()

        if not line:
            continue

        lower = line.lower()

        # استبعد الكلمات العامة
        if lower in GENERIC_TITLES:
            continue

        # استبعد bullets
        if line.startswith("-"):
            continue

        # عنوان منطقي
        if 10 < len(line) < 80 and line[0].isupper():
            return line

    return "General Information"



def build_chunks(text: str, source: str):
    chunks = []
    layers = split_layers(text)

    for layer_name, layer_text in layers.items():
        sections = split_sections(layer_text)

        for sec in sections:
            internal_title = extract_internal_title(sec["text"])

            chunk_text = (
                f"{internal_title}\n\n"
                f"{sec['text']}"
            )

            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "source": source,
                    "layer": layer_name,
                    "section_title": sec["section_title"],
                    "internal_title": internal_title,
                    "chunk_id": f"{layer_name}_S{sec['section_id']}"
                }
            })

    return chunks



