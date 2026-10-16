# Uploads with Russian filenames

The memorial upload endpoint included the user filename in the storage key. Supabase rejects Cyrillic object keys with HTTP400 and an empty S3 error, while the same synthetic PNG with an ASCII key succeeds.

The endpoint now stores media under UUID.extension and retains the supplied name in Media.file_name. Original content and derived thumbnail handling stay intact. No data migration or change to existing media is required.

Regression tests exercise Cyrillic, emoji and ASCII names, ASCII-only original/thumbnail storage keys, original byte preservation and display names. Live diagnostic used only a synthetic2x2PNG; the successful diagnostic object was removed.
