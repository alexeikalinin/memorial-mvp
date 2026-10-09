"""Supported Fish TTS engines and compatibility with retired S1 settings."""
DEFAULT_FISH_MODEL = 's2-pro'


def resolve_fish_model(selected, configured):
    model = selected or configured or DEFAULT_FISH_MODEL
    return DEFAULT_FISH_MODEL if model == 's1' else model
