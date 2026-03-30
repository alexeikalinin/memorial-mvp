"""
Хэндлеры команд и сообщений Telegram-бота.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from telegram import Update, ChatAction
from telegram.constants import ChatAction as CA
from telegram.ext import ContextTypes

from .api_client import get_memorials, get_memorial, avatar_chat, build_audio_url
from .session import get_session, set_session, clear_session
from .keyboards import memorial_keyboard, settings_keyboard


# --- /start ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    args = context.args  # deep link: ["memorial_1"]

    if args and args[0].startswith("memorial_"):
        try:
            memorial_id = int(args[0].split("_")[1])
            memorial = await get_memorial(memorial_id)
            if not memorial:
                await update.message.reply_text("Мемориал не найден. Выберите другой /start")
                return
            name = memorial.get("full_name") or f"Мемориал #{memorial_id}"
            session = await get_session(chat_id) or {}
            session["memorial_id"] = memorial_id
            session.setdefault("voice_mode", False)
            session.setdefault("include_family", False)
            await set_session(chat_id, session)
            await update.message.reply_text(
                f"🕯️ Теперь вы общаетесь с {name}.\n\n"
                f"Напишите что-нибудь или задайте вопрос.\n"
                f"/help — список команд"
            )
            return
        except (ValueError, IndexError):
            pass

    # Нет deep link — показываем список мемориалов
    try:
        memorials = await get_memorials()
    except Exception as e:
        await update.message.reply_text(f"Не удалось загрузить мемориалы: {e}")
        return

    if not memorials:
        await update.message.reply_text(
            "Мемориалов пока нет. Создайте первый на сайте."
        )
        return

    await update.message.reply_text(
        "👋 Добро пожаловать!\n\nВыберите мемориал, с которым хотите пообщаться:",
        reply_markup=memorial_keyboard(memorials),
    )


# --- /change ---

async def change(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        memorials = await get_memorials()
    except Exception as e:
        await update.message.reply_text(f"Ошибка загрузки: {e}")
        return

    if not memorials:
        await update.message.reply_text("Мемориалов пока нет.")
        return

    await update.message.reply_text(
        "Выберите мемориал:",
        reply_markup=memorial_keyboard(memorials),
    )


# --- /voice ---

async def voice_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = await get_session(chat_id) or {}
    if not session.get("memorial_id"):
        await update.message.reply_text("Сначала выберите мемориал /start")
        return
    session["voice_mode"] = not session.get("voice_mode", False)
    await set_session(chat_id, session)
    status = "включена 🔊" if session["voice_mode"] else "выключена 🔇"
    await update.message.reply_text(f"Озвучка {status}")


# --- /family ---

async def family_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = await get_session(chat_id) or {}
    if not session.get("memorial_id"):
        await update.message.reply_text("Сначала выберите мемориал /start")
        return
    session["include_family"] = not session.get("include_family", False)
    await set_session(chat_id, session)
    status = "включены 👨‍👩‍👧" if session["include_family"] else "выключены"
    await update.message.reply_text(f"Воспоминания родственников {status}")


# --- /help ---

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📋 *Команды бота:*\n\n"
        "/start — выбрать мемориал\n"
        "/change — сменить мемориал\n"
        "/voice — вкл/выкл озвучку ответов\n"
        "/family — вкл/выкл воспоминания родственников\n"
        "/help — этот список\n\n"
        "Просто напишите сообщение — и аватар ответит.",
        parse_mode="Markdown",
    )


# --- Callback (inline keyboard) ---

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    if query.data.startswith("select_memorial:"):
        try:
            memorial_id = int(query.data.split(":")[1])
        except (ValueError, IndexError):
            await query.edit_message_text("Ошибка выбора мемориала.")
            return

        memorial = await get_memorial(memorial_id)
        if not memorial:
            await query.edit_message_text("Мемориал не найден.")
            return

        name = memorial.get("full_name") or f"Мемориал #{memorial_id}"
        session = await get_session(chat_id) or {}
        session["memorial_id"] = memorial_id
        session.setdefault("voice_mode", False)
        session.setdefault("include_family", False)
        await set_session(chat_id, session)
        await query.edit_message_text(
            f"✓ Выбран: *{name}*\n\nНапишите что-нибудь или задайте вопрос.\n/help — список команд",
            parse_mode="Markdown",
        )

    elif query.data == "toggle_voice":
        session = await get_session(chat_id) or {}
        session["voice_mode"] = not session.get("voice_mode", False)
        await set_session(chat_id, session)
        await query.edit_message_reply_markup(
            reply_markup=settings_keyboard(session["voice_mode"], session.get("include_family", False))
        )

    elif query.data == "toggle_family":
        session = await get_session(chat_id) or {}
        session["include_family"] = not session.get("include_family", False)
        await set_session(chat_id, session)
        await query.edit_message_reply_markup(
            reply_markup=settings_keyboard(session.get("voice_mode", False), session["include_family"])
        )

    elif query.data == "no_memorials":
        await query.edit_message_text("Мемориалов нет. Создайте первый на сайте.")


# --- Текстовые сообщения ---

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    session = await get_session(chat_id)

    if not session or not session.get("memorial_id"):
        await update.message.reply_text(
            "Сначала выберите мемориал: /start"
        )
        return

    await context.bot.send_chat_action(chat_id=chat_id, action=CA.TYPING)

    try:
        result = await avatar_chat(
            memorial_id=session["memorial_id"],
            question=update.message.text,
            include_audio=session.get("voice_mode", False),
            include_family=session.get("include_family", False),
        )
    except Exception as e:
        await update.message.reply_text(f"Ошибка при обращении к аватару: {e}")
        return

    answer = result.get("answer", "")
    if answer:
        await update.message.reply_text(answer)

    audio_url = result.get("audio_url")
    if audio_url:
        try:
            full_url = build_audio_url(audio_url)
            await context.bot.send_audio(chat_id=chat_id, audio=full_url)
        except Exception as e:
            # Аудио опционально — не ломаем чат
            print(f"Warning: could not send audio: {e}")
