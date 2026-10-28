from app.services.generated_audio import generated_audio_dir, find_generated_audio


def test_volume_audio_survives_workdir_change(client, tmp_path, monkeypatch):
    volume = tmp_path / 'volume'
    volume.mkdir()
    monkeypatch.setenv('RAILWAY_VOLUME_MOUNT_PATH', str(volume))
    target = generated_audio_dir()
    target.mkdir()
    (target / 'cached_test.mp3').write_bytes(b'persisted-audio')
    other = tmp_path / 'new-container'
    other.mkdir()
    monkeypatch.chdir(other)
    assert find_generated_audio('cached_test.mp3').read_bytes() == b'persisted-audio'
    response = client.get('/api/v1/media/audio/cached_test.mp3')
    assert response.status_code == 200 and response.content == b'persisted-audio'


def test_old_local_audio_remains_readable(tmp_path, monkeypatch):
    monkeypatch.setenv('RAILWAY_VOLUME_MOUNT_PATH', str(tmp_path / 'volume'))
    old = tmp_path / 'legacy-audio'
    old.mkdir()
    (old / 'old.mp3').write_bytes(b'legacy')
    assert find_generated_audio('old.mp3', old).read_bytes() == b'legacy'


def test_oauth_transaction_tables_protected_for_postgres():
    from app.yandex_auth_models import protect_yandex_tables
    class Connection:
        statements = []
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, sql): self.statements.append(str(sql))
    class Engine:
        class dialect: name = 'postgresql'
        def begin(self): return conn
    conn = Connection()
    protect_yandex_tables(Engine())
    assert set(conn.statements) == {f'ALTER TABLE {table} ENABLE ROW LEVEL SECURITY' for table in ('yandex_identities','yandex_attempts','yandex_tickets')}
