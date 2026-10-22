"""Read an explicitly requested approved speech verbatim, without generation."""
import re


def requested_thank_you_speech(question, memories):
    question = question.casefold().replace('ё', 'е')
    if not (re.search(r'\b(скажи|расскажи|произнеси|прочитай|зачитай|озвучь)\b', question)
            and re.search(r'\bблагодарственн\w*\s+речь\b', question)):
        return None
    # Summaries, transformations and questions about a speech remain normal chat.
    if re.search(r'\b(кратко|коротко|сократи\w*|перескажи\w*|придумай|измени|переведи|не)\b', question):
        return None
    matches = [memory for memory in memories
               if memory.status == 'approved' and (memory.content or '').strip()
               and re.search(r'\bблагодарственн\w*\s+речь\b',
                             (memory.title or '').casefold().replace('ё', 'е'))]
    # Never silently choose between different saved speeches.
    return matches[0] if len(matches) == 1 else None
