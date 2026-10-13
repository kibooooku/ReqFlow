"""Password and opaque-session primitives; no plaintext passwords at rest."""
import hashlib
import hmac
import secrets
import time

def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1, dklen=32)
    return f'scrypt${salt.hex()}${digest.hex()}'

def verify_password(password, stored):
    try:
        _, salt, expected = stored.split('$')
        actual = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1, dklen=32)
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False

def token_hash(token):
    return hashlib.sha256(token.encode()).hexdigest()

def new_session(conn, user_id):
    token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    conn.execute('DELETE FROM sessions WHERE expires_at < ?', (time.time(),))
    conn.execute('INSERT INTO sessions VALUES(?,?,?,?)', (token_hash(token), user_id, csrf, time.time()+8*3600))
    return token, csrf

def public_user(row):
    return {key: (bool(row[key]) if key == 'is_admin' else row[key]) for key in ('id','username','name','is_admin')}
