# -*- coding: utf-8 -*-
"""Извлекает сессионную cookie CODESYS 4 из профиля WebView2 (DPAPI + AES-GCM)."""
import json, base64, sqlite3, shutil, tempfile, os, sys

# Путь к профилю WebView2 CODESYS 4 (…\CODESYS-4\webview\<id>\EBWebView).
# Подставьте свой: python get_c4_session.py <profile_dir> или env C4_WEBVIEW_PROFILE.
PROFILE = os.environ.get("C4_WEBVIEW_PROFILE") or (sys.argv[1] if len(sys.argv) > 1 else None)
if not PROFILE:
    sys.exit("usage: python get_c4_session.py <EBWebView profile dir>")

def dpapi_decrypt(data: bytes) -> bytes:
    import ctypes, ctypes.wintypes as wt

    class DATA_BLOB(ctypes.Structure):
        _fields_ = [("cbData", wt.DWORD), ("pbData", ctypes.POINTER(ctypes.c_char))]

    blob_in = DATA_BLOB(len(data), ctypes.cast(ctypes.create_string_buffer(data, len(data)), ctypes.POINTER(ctypes.c_char)))
    blob_out = DATA_BLOB()
    if not ctypes.windll.crypt32.CryptUnprotectData(ctypes.byref(blob_in), None, None, None, None, 0, ctypes.byref(blob_out)):
        raise RuntimeError("CryptUnprotectData failed")
    return ctypes.string_at(blob_out.pbData, blob_out.cbData)

def get_aes_key():
    state = json.load(open(os.path.join(PROFILE, "Local State"), encoding="utf-8"))
    enc_key = base64.b64decode(state["os_crypt"]["encrypted_key"])
    assert enc_key.startswith(b"DPAPI"), "unexpected key format"
    return dpapi_decrypt(enc_key[5:])

def decrypt_cookie(value: bytes, key: bytes) -> str:
    # Chromium >= 80: v10/v11 = AES-256-GCM, префикс 3 байта
    if value[:3] in (b"v10", b"v11"):
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = value[3:15]
        ciphertext = value[15:]
        return AESGCM(key).decrypt(nonce, ciphertext, None).decode("utf-8", "replace")
    # старый формат — чистый DPAPI
    try:
        return dpapi_decrypt(value).decode("utf-8", "replace")
    except Exception:
        return "<undecryptable>"

def main():
    key = get_aes_key()
    src = os.path.join(PROFILE, "Default", "Network", "Cookies")
    tmp = os.path.join(tempfile.gettempdir(), "c4_cookies_copy.sqlite")
    shutil.copyfile(src, tmp)
    con = sqlite3.connect(tmp)
    cur = con.execute(
        "SELECT host_key, name, encrypted_value, is_session, expires_utc FROM cookies WHERE host_key LIKE '%127.0.0.1%' OR host_key LIKE '%localhost%'"
    )
    rows = cur.fetchall()
    con.close()
    os.unlink(tmp)
    print(f"cookie rows for localhost: {len(rows)}")
    for host, name, enc, is_sess, exp in rows:
        try:
            val = decrypt_cookie(enc, key)
        except Exception as e:
            val = f"<error: {e}>"
        print(f"  host={host} name={name} session={is_sess} value={val[:80]}")

if __name__ == "__main__":
    main()
