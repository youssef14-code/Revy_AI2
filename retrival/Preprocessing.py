# preprocessing.py
import re

def preprocess_text(text: str) -> str:
    text = re.sub(r"\n{2,}", "\n", text)
    text = text.replace("•", "-")
    text = text.strip()
    return text


