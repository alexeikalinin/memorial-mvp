"""
Лёгкая локализация сообщений API (ошибки, статусы) для RU/EN.

Язык запроса определяется заголовком `X-Lang`, который шлёт фронтенд
(см. frontend/src/api/client.js) на основе текущего UI-языка пользователя
(см. frontend/src/contexts/LanguageContext.jsx). По умолчанию — русский,
так как продукт запускается на русскоязычном рынке.

Использование:
    from app.i18n import Lang, tr

    def endpoint(lang: str = Depends(get_lang)):
        raise HTTPException(status_code=400, detail=tr(lang, "email_taken"))
"""
from fastapi import Header

DEFAULT_LANG = "ru"

MESSAGES = {
    "email_taken": {
        "ru": "Этот email уже зарегистрирован",
        "en": "Email already registered",
    },
    "username_taken": {
        "ru": "Это имя пользователя уже занято",
        "en": "Username already taken",
    },
    "incorrect_credentials": {
        "ru": "Неверный email или пароль",
        "en": "Incorrect email or password",
    },
    "google_oauth_not_configured": {
        "ru": "Вход через Google не настроен",
        "en": "Google OAuth not configured",
    },
    "google_code_exchange_failed": {
        "ru": "Не удалось обменять код авторизации Google",
        "en": "Failed to exchange Google code",
    },
    "google_userinfo_failed": {
        "ru": "Не удалось получить данные профиля Google",
        "en": "Failed to fetch Google user info",
    },
    "google_incomplete_profile": {
        "ru": "Неполный профиль Google",
        "en": "Incomplete Google profile",
    },
    "verification_token_invalid": {
        "ru": "Недействительный или просроченный токен подтверждения",
        "en": "Invalid or expired verification token",
    },
    "verification_token_expired": {
        "ru": "Токен подтверждения истёк. Запросите новый.",
        "en": "Verification token has expired. Please request a new one.",
    },
    "email_already_verified": {
        "ru": "Email уже подтверждён",
        "en": "Email already verified",
    },
    "email_verified_success": {
        "ru": "Email успешно подтверждён",
        "en": "Email verified successfully",
    },
    "verification_email_sent": {
        "ru": "Письмо с подтверждением отправлено",
        "en": "Verification email sent",
    },
    "reset_token_invalid": {
        "ru": "Недействительный или просроченный токен восстановления",
        "en": "Invalid or expired reset token",
    },
    "reset_token_expired": {
        "ru": "Токен восстановления истёк. Запросите восстановление пароля заново.",
        "en": "Reset token has expired. Please request a new password reset.",
    },
    "password_reset_email_sent": {
        "ru": "Если этот email зарегистрирован, вы получите письмо со ссылкой для восстановления пароля.",
        "en": "If this email is registered, you will receive a password reset link shortly.",
    },
    "password_updated_success": {
        "ru": "Пароль успешно обновлён",
        "en": "Password updated successfully",
    },
    "memorial_not_found": {
        "ru": "Мемориал не найден",
        "en": "Memorial not found",
    },
    "media_not_found": {
        "ru": "Медиафайл не найден",
        "en": "Media not found",
    },
    "memory_not_found": {
        "ru": "Воспоминание не найдено",
        "en": "Memory not found",
    },
    "access_denied": {
        "ru": "Недостаточно прав для этого действия",
        "en": "Access denied",
    },
    "already_have_access": {
        "ru": "У вас уже есть доступ к этому мемориалу",
        "en": "You already have access to this memorial",
    },
    "access_request_sent": {
        "ru": "Запрос на доступ отправлен",
        "en": "Access request sent",
    },
    "qr_lib_missing": {
        "ru": "Библиотека для QR-кода не установлена. Выполните: pip install 'qrcode[pil]'",
        "en": "QR code library not installed. Run: pip install 'qrcode[pil]'",
    },
    "file_extension_not_allowed": {
        "ru": "Расширение файла «{ext}» не разрешено. Разрешены: {allowed}",
        "en": "File extension '{ext}' not allowed. Allowed: {allowed}",
    },
    "file_too_large": {
        "ru": "Размер файла превышает максимально допустимый ({max_size} байт)",
        "en": "File size exceeds maximum allowed size of {max_size} bytes",
    },
    "invalid_image_file": {
        "ru": "Некорректный файл изображения: {error}",
        "en": "Invalid image file: {error}",
    },
    "invalid_video_file": {
        "ru": "Некорректный видеофайл: {error}",
        "en": "Invalid video file: {error}",
    },
    "file_upload_error": {
        "ru": "Ошибка при загрузке файла: {error}",
        "en": "Error uploading file: {error}",
    },
    "invite_token_invalid": {
        "ru": "Недействительный инвайт-токен",
        "en": "Invalid invite token",
    },
    "invite_token_expired": {
        "ru": "Срок действия инвайт-токена истёк",
        "en": "Invite token expired",
    },
    "invite_no_memories_permission": {
        "ru": "Этот инвайт не позволяет добавлять воспоминания",
        "en": "Invite does not allow adding memories",
    },
    "authentication_required": {
        "ru": "Требуется авторизация",
        "en": "Authentication required",
    },
    "memorial_is_private": {
        "ru": "Мемориал закрыт для публичного доступа",
        "en": "Memorial is private",
    },
    "media_not_found_in_memorial": {
        "ru": "Медиафайл не найден в этом мемориале",
        "en": "Media not found in this memorial",
    },
    "audio_file_not_found": {
        "ru": "Аудиофайл не найден",
        "en": "Audio file not found",
    },
    "invalid_media_id": {
        "ru": "Некорректный ID медиафайла",
        "en": "Invalid media ID",
    },
    "media_file_not_found_on_disk": {
        "ru": "Медиафайл не найден на диске",
        "en": "Media file not found on disk",
    },
}


def get_lang(x_lang: str = Header(default=DEFAULT_LANG, alias="X-Lang")) -> str:
    """FastAPI dependency: возвращает 'ru' или 'en' на основе заголовка X-Lang."""
    return "en" if x_lang == "en" else "ru"


def tr(lang: str, key: str, **params) -> str:
    """Перевести ключ сообщения на нужный язык; при отсутствии ключа возвращает сам ключ.
    Поддерживает форматирование через `{name}`-плейсхолдеры, передаваемые как kwargs."""
    entry = MESSAGES.get(key)
    if not entry:
        return key
    template = entry.get(lang, entry["ru"])
    return template.format(**params) if params else template
