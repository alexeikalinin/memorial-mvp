"""
Inline keyboards для Telegram-бота.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def memorial_keyboard(memorials: list[dict]) -> InlineKeyboardMarkup:
    """Клавиатура для выбора мемориала."""
    buttons = []
    for m in memorials:
        name = m.get("full_name") or m.get("name") or f"Мемориал #{m['id']}"
        birth = m.get("birth_year", "")
        death = m.get("death_year", "")
        years = f" ({birth}–{death})" if birth or death else ""
        label = f"{name}{years}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"select_memorial:{m['id']}")])
    if not buttons:
        buttons.append([InlineKeyboardButton("Нет мемориалов", callback_data="no_memorials")])
    return InlineKeyboardMarkup(buttons)


def settings_keyboard(voice: bool, family: bool) -> InlineKeyboardMarkup:
    """Клавиатура настроек бота."""
    voice_label = f"🔊 Голос: {'вкл' if voice else 'выкл'}"
    family_label = f"👨‍👩‍👧 Семья: {'вкл' if family else 'выкл'}"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(voice_label, callback_data="toggle_voice")],
        [InlineKeyboardButton(family_label, callback_data="toggle_family")],
    ])
