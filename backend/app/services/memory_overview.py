"""Recognize archive overview requests without broadening specific questions."""
import re


def is_memory_overview_question(question: str) -> bool:
    text = re.sub(r"[?!.,:;]+", "", question.lower())
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^(пожалуйста |please )", "", text)
    return bool(re.fullmatch(
        r"(?:расскажи (?:мне )?(?:что (?:ты )?помнишь о себе|о себе|о своей жизни)|"
        r"что (?:ты )?помнишь о себе|какие (?:у тебя )?есть воспоминания|"
        r"tell me (?:about yourself|about your life|what you remember about yourself)|"
        r"what do you remember about yourself)", text,
    ))


def overview_context(memories, memorial_id, max_chars=18000):
    """Use only approved archive entries, with a bounded share for every entry."""
    entries = sorted(
        (m for m in memories if m.status == 'approved' and (m.content or '').strip()),
        key=lambda m: m.id,
    )[:30]
    if not entries:
        return []
    per_entry = max_chars // len(entries)
    chunks = []
    for memory in entries:
        text = memory.content.strip()
        if len(text) > per_entry:
            text = text[:per_entry]
            # Avoid presenting a half sentence as evidence.
            end = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
            if end >= 0:
                text = text[:end + 1]
        chunks.append({'text': text, 'memory_id': memory.id, 'title': memory.title,
                       'score': 1.0, 'source_memorial_id': memorial_id})
    return chunks
