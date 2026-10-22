import asyncio
import json
import subprocess
from unittest.mock import AsyncMock

import pytest

from app.services.long_speech import speech_chunks, join_speech_audio


@pytest.mark.parametrize('text', ['Слово. ' * 1400, 'я' * 9001, 'Текст\n\n' * 2000, 'я' * 2999 + '\n' * 4 + 'Конец.'])
def test_split_preserves_all_characters(text):
    chunks = speech_chunks(text)
    assert ''.join(chunks) == text
    assert all(0 < len(chunk) <= 3000 for chunk in chunks)


@pytest.mark.parametrize('provider', ['fish_audio', 'elevenlabs'])
def test_long_text_is_not_truncated_and_keeps_voice_settings(monkeypatch, provider):
    from app.services import ai_tasks
    synth = AsyncMock(return_value=b'audio')
    join = AsyncMock(return_value=b'full-mp3')
    monkeypatch.setattr(ai_tasks, f'generate_speech_{provider}', synth)
    monkeypatch.setattr('app.services.long_speech.join_speech_audio', join)
    text = 'Спасибо за то, что пришли.\n\n' * 240 + 'Это последнее предложение.'
    result = asyncio.run(ai_tasks.generate_speech(text, voice_id='chosen', provider=provider, speed=.9, model='s2.1-pro'))
    assert result == b'full-mp3'
    sent = [call.args[0] for call in synth.call_args_list]
    assert ''.join(sent) == text
    assert all(len(chunk) <= 3000 for chunk in sent)
    for call in synth.call_args_list:
        assert call.kwargs['voice_id'] == 'chosen'
        if provider == 'fish_audio':
            assert call.kwargs['speed'] == .9
            assert call.kwargs['model'] == 's2.1-pro'
    join.assert_awaited_once()


def test_joined_audio_contains_both_parts(tmp_path):
    part = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i',
                           'sine=frequency=440:duration=0.4', '-f', 'mp3', 'pipe:1'],
                          check=True, capture_output=True).stdout
    joined = asyncio.run(join_speech_audio([part, part]))
    output = tmp_path / 'joined.mp3'
    output.write_bytes(joined)
    info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_format',
                                     '-of', 'json', str(output)], check=True, capture_output=True).stdout)
    assert .75 < float(info['format']['duration']) < 1.1


def test_provider_failure_does_not_return_partial_audio(monkeypatch):
    from app.services import ai_tasks
    synth = AsyncMock(side_effect=[b'first-part', ValueError('provider unavailable')])
    monkeypatch.setattr(ai_tasks, 'generate_speech_fish_audio', synth)
    with pytest.raises(ValueError, match='provider unavailable'):
        asyncio.run(ai_tasks.generate_speech('word ' * 1000, provider='fish_audio'))
