"""Generated speech lives on the attached Railway volume across deployments."""
import os
from pathlib import Path


def generated_audio_dir():
    mount = os.getenv('RAILWAY_VOLUME_MOUNT_PATH')
    return Path(mount) / 'generated_audio' if mount else Path('uploads/audio')


def find_generated_audio(filename, legacy_dir=None):
    name = Path(filename).name
    current = generated_audio_dir() / name
    legacy = (Path(legacy_dir) if legacy_dir is not None else Path('uploads/audio')) / name
    return current if current.is_file() else legacy if legacy.is_file() else current
