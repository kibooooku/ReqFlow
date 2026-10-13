"""Independent review regressions: desired behavior, never injected defects."""
import asyncio
from contextlib import contextmanager

from fastapi.testclient import TestClient

from app import db
from app.main import create_app


def test_document_role_is_rechecked_inside_write_transaction(actors, monkeypatch):
    """A committed role downgrade at the write boundary must prevent the write."""
    original_transaction = db.transaction
    scheduled = []

    @contextmanager
    def downgrade_before_begin(connection):
        if not scheduled:
            scheduled.append(True)
            other = db.connect(actors['db'])
            try:
                with original_transaction(other):
                    other.execute("UPDATE members SET role='viewer' WHERE project_id=1 AND user_id=2")
            finally:
                other.close()
        with original_transaction(connection):
            yield

    monkeypatch.setattr(db, 'transaction', downgrade_before_begin)
    response = actors['analyst'].post('/projects/1/documents', {'title': 'must not survive revoked permission'})
    assert scheduled, 'The regression must exercise the write boundary'
    assert response.status_code == 403, response.text
    documents = actors['viewer'].get('/projects/1/documents').json()
    assert not any(x['title'] == 'must not survive revoked permission' for x in documents)


def test_non_ascii_csrf_header_returns_forbidden_not_server_error(actors):
    with TestClient(actors['app'], raise_server_exceptions=False) as client:
        client.cookies.update(actors['analyst'].client.cookies)
        response = client.post('/api/auth/logout', json={}, headers=[(b'x-csrf-token', b'\xff')])
        assert response.status_code == 403, response.text
        assert response.json()['detail']
        # Malformed CSRF input must not invalidate a legitimate session.
        assert client.get('/api/auth/me').status_code == 200


def test_password_whitespace_is_preserved_as_credential_data(actors):
    password = ' ExactSpacePass2026! '
    response = actors['admin'].post('/users', {
        'username': 'space_password_user', 'name': '凭据测试', 'password': password,
    })
    assert response.status_code == 201, response.text
    with TestClient(actors['app']) as client:
        exact = client.post('/api/auth/login', json={'username': 'space_password_user', 'password': password})
        assert exact.status_code == 200
        changed = client.post('/api/auth/login', json={'username': 'space_password_user', 'password': password.strip()})
        assert changed.status_code == 401, 'Distinct passwords must not be normalized to the same credential'


def test_body_limit_stops_reading_after_crossing_threshold(tmp_path):
    """Use raw ASGI receive to measure what the application actually consumes."""
    app = create_app(tmp_path / 'body-limit.db', seed_demo=False)
    consumed = []
    messages = []
    chunk = b'x' * (64 * 1024)

    async def receive():
        index = len(consumed)
        if index < 20:
            consumed.append(index)
            return {'type': 'http.request', 'body': chunk, 'more_body': index < 19}
        return {'type': 'http.disconnect'}

    async def send(message):
        messages.append(message)

    scope = {
        'type': 'http', 'asgi': {'version': '3.0'}, 'http_version': '1.1',
        'method': 'POST', 'scheme': 'http', 'path': '/api/auth/login',
        'raw_path': b'/api/auth/login', 'query_string': b'', 'root_path': '',
        'headers': [(b'host', b'testserver'), (b'content-type', b'application/json')],
        'client': ('127.0.0.1', 50000), 'server': ('testserver', 80),
    }
    asyncio.run(app(scope, receive, send))
    start = next(x for x in messages if x['type'] == 'http.response.start')
    assert start['status'] == 413
    assert len(consumed) <= 5, f'Consumed {len(consumed)} chunks ({len(consumed) * len(chunk)} bytes) before rejecting a 256KB-limited body'
