# -*- coding: utf-8 -*-
"""Локальный WS-прокси для перехвата трафика CODESYS 4.

Схема: Chrome (--proxy-server=127.0.0.1:8791) -> CONNECT localhost:<c4port>
-> прокси туннелирует TCP и параллельно парсит WS-фреймы (трафик plaintext).

Лог: codesys4/proxy_traffic.log  (C> / >S — клиент->сервер / сервер->клиент)
"""
import asyncio, socket, struct, sys, time, os

LISTEN = ("127.0.0.1", 8791)
LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "proxy_traffic.log")

logf = open(LOG, "a", encoding="utf-8", buffering=1)

def log(direction, payload):
    ts = time.strftime("%H:%M:%S")
    try:
        text = payload.decode("utf-8", errors="replace")
    except Exception:
        text = repr(payload)
    for line in text.splitlines():
        logf.write(f"{ts} {direction} {line}\n")

async def read_http_headers(reader):
    data = b""
    while b"\r\n\r\n" not in data:
        chunk = await reader.read(4096)
        if not chunk:
            break
        data += chunk
        if len(data) > 65536:
            break
    if b"\r\n\r\n" in data:
        head, leftover = data.split(b"\r\n\r\n", 1)
        return head + b"\r\n\r\n", leftover
    return data, b""

def ws_frames(buf):
    """Достаём полные текстовые WS-фреймы из буфера. Возврат: (frames, rest)."""
    frames, i = [], 0
    while True:
        if len(buf) < i + 2:
            break
        b0, b1 = buf[i], buf[i+1]
        opcode = b0 & 0x0F
        masked = b1 & 0x80
        ln = b1 & 0x7F
        p = i + 2
        if ln == 126:
            if len(buf) < p + 2: break
            ln = struct.unpack(">H", buf[p:p+2])[0]; p += 2
        elif ln == 127:
            if len(buf) < p + 8: break
            ln = struct.unpack(">Q", buf[p:p+8])[0]; p += 8
        mask = b""
        if masked:
            if len(buf) < p + 4: break
            mask = buf[p:p+4]; p += 4
        if len(buf) < p + ln:
            break
        payload = buf[p:p+ln]
        if masked:
            payload = bytes(b ^ mask[j % 4] for j, b in enumerate(payload))
        if opcode == 1:  # text
            frames.append(payload)
        elif opcode == 9:  # ping -> pong handled by relay (pass-through)
            pass
        i = p + ln
    return frames, buf[i:]

async def tunnel(client_r, client_w, server_r, server_w, c2s_buf, s2c_buf, tag):
    async def pipe(r, w, buf_name, direction, is_client_side):
        nonlocal c2s_buf, s2c_buf
        while True:
            data = await r.read(65536)
            if not data:
                break
            w.write(data)
            await w.drain()
            if is_client_side:
                c2s_buf += data
                frames, c2s_buf = ws_frames(c2s_buf)
                for f in frames:
                    log("C>", f)
            else:
                s2c_buf += data
                frames, s2c_buf = ws_frames(s2c_buf)
                for f in frames:
                    log(">S", f)
    try:
        await asyncio.gather(
            pipe(client_r, server_w, "c2s", "C>", True),
            pipe(server_r, client_w, "s2c", ">S", False),
        )
    except Exception:
        pass
    finally:
        for w in (client_w, server_w):
            try: w.close()
            except Exception: pass

async def handle(client_r, client_w):
    try:
        head, leftover = await read_http_headers(client_r)
        first = head.split(b"\r\n", 1)[0]
        if first.startswith(b"CONNECT"):
            target = first.split()[1].decode()
            host, port = target.rsplit(":", 1)
            port = int(port)
            server_r, server_w = await asyncio.open_connection(host, port)
            client_w.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await client_w.drain()
            log("==", f"CONNECT {target}".encode())
            if leftover:
                server_w.write(leftover)
                await server_w.drain()
            await tunnel(client_r, client_w, server_r, server_w, leftover, b"", target)
        else:
            # обычный HTTP-прокси (GET/POST http://...)
            line = first.decode(errors="replace")
            parts = line.split()
            url = parts[1]
            from urllib.parse import urlparse
            pu = urlparse(url)
            host = pu.hostname
            port = pu.port or 80
            path = (pu.path or "/") + (("?" + pu.query) if pu.query else "")
            new_head = head.replace(line.encode(), f"{parts[0]} {path} HTTP/1.1".encode(), 1)
            # убраем proxy-connection заголовок
            new_head = new_head.replace(b"Proxy-Connection:", b"X-Old-Conn:")
            server_r, server_w = await asyncio.open_connection(host, port)
            server_w.write(new_head)
            await server_w.drain()
            if leftover:
                server_w.write(leftover)
                await server_w.drain()
            log("C>", f"HTTP {line}".encode())
            # релей HTTP ответа целиком (логируем заголовки + текстовое тело)
            async def http_relay():
                while True:
                    data = await server_r.read(65536)
                    if not data:
                        break
                    client_w.write(data)
                    await client_w.drain()
                    log(">S", data[:2000])
                client_w.close()
            await asyncio.gather(http_relay(), _drain(client_r, server_w))
    except Exception as e:
        try:
            client_w.close()
        except Exception:
            pass

async def _drain(r, w):
    while True:
        data = await r.read(65536)
        if not data:
            break
        w.write(data)
        await w.drain()
        log("C>", data[:2000])

async def main():
    srv = await asyncio.start_server(handle, *LISTEN)
    logf.write(f"=== proxy started on {LISTEN} ===\n")
    async with srv:
        await srv.serve_forever()

if __name__ == "__main__":
    asyncio.run(main())
