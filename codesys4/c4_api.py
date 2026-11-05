# -*- coding: utf-8 -*-
"""c4_api.py — полноценная обвязка для работы с CODESYS 4 через его JSON-RPC/HTTP API.

Архитектура C4: c4-cli.exe (standalone-session) поднимает локальный ASP.NET-бэкенд
с динамическим портом (127.0.0.1:5xxxx). Фронт — Angular-приложение, общение —
WebSocket `ws://127.0.0.1:<port>/api/JsonRpc` (сабпротокол `tab.<uuid>`).
Авторизация: одноразовый InitToken из URL -> POST /api/UserSessions -> cookie
codesys_4_auth + заголовок XSRF-TOKEN. Файлы читаются/пишутся НЕ через JSON-RPC,
а по HTTP: GET/PUT /api/FileSystemHttp?fileUrl=... (нужны Cookie, X-XSRF-TOKEN,
X-C4-Tab-Id).

Ключевые грабли (проверено экспериментально, 2026-10-30):
  * URL проекта в AddProject ОБЯЗАН заканчиваться на '/' (file:///.../proj.fbsdev/),
    иначе WorkspaceMetaManager падает с "Path is outside a project",
    а Compile таймаутится ("did not become available in the workspace").
  * Компилятор кэширует language model. Правка файла через PUT сама по себе
    компиляцию НЕ запускает (Compile возвращает true, но сборка no-op).
    Надёжный рецепт «применить изменения»: RemoveProject + AddProject + Compile —
    LM пересобирается с диска, библиотеки подтягиваются автоматически
    (из extension-пакетов, быстро).
  * Диагностика компиляции приходит нотификациями `_c4-callback/call` на
    подписки CODESYS.C4.Modules.MessagePool.{Run,Status}MessagePool.Changes
    с параметрами [callbackId, category]; категории: Build, Library Resolution, Compile.
"""
import asyncio
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

import websockets

_C4_CLI = os.environ.get("C4_CLI", "c4-cli")
_CAPTURE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "c4capture.cmd")

COMPILER = "CODESYS.C4.Modules.Compiler.ICompilerService"
WORKSPACE = "CODESYS.C4.Modules.WorkspaceManager"
OBJMODEL = "CODESYS.C4.Sdk.ObjectModel.Services.IObjectModelService"
FILESYSTEM = "CODESYS.C4.Sdk.FileSystem.IFileSystem"
WATCHER = "CODESYS.C4.Modules.FileSystem.IFileSystemWatcher"
MSGPOOL = "CODESYS.C4.Modules.MessagePool"


def project_url(path):
    """file:/// URL папки проекта — обязательно с завершающим '/'."""
    p = os.path.abspath(path).replace("\\", "/")
    if not p.endswith("/"):
        p += "/"
    return "file:///" + p.lstrip("/") if not p.startswith("file:") else p


class C4:
    """Клиент одной сессии CODESYS 4."""

    def __init__(self, port, cookie, xsrf, tab=None):
        self.port = port
        self.cookie = cookie
        self.xsrf = xsrf
        self.tab = tab or str(uuid.uuid4())
        self.ws = None
        self._id = 0
        self._cb = 0
        self._pending_notify = []   # необработанные нотификации (только чтение)

    # ---------- транспорт ----------
    async def connect(self):
        headers = {
            "Cookie": self.cookie,
            "Origin": f"http://127.0.0.1:{self.port}",
            "X-XSRF-TOKEN": self.xsrf,
            "X-C4-Tab-Id": self.tab,
        }
        self.ws = await websockets.connect(
            f"ws://127.0.0.1:{self.port}/api/JsonRpc",
            subprotocols=[f"tab.{self.tab}"],
            additional_headers=headers, max_size=100_000_000)
        return self

    async def call(self, method, params=None, timeout=30):
        self._id += 1
        mid = self._id
        msg = {"jsonrpc": "2.0", "id": mid, "method": method}
        if params is not None:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))
        while True:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            resp = json.loads(raw)
            if resp.get("id") == mid:
                return resp
            self._pending_notify.append(resp)

    async def close(self):
        if self.ws:
            await self.ws.close()

    def _next_cb(self):
        self._cb += 1
        return f"_c4-callback/{self._cb}"

    # ---------- HTTP-файлы ----------
    def _http(self, verb, file_url, body=None, content_type="text/plain; charset=utf-8"):
        q = urllib.parse.quote(file_url, safe="")
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}/api/FileSystemHttp?fileUrl={q}",
            data=body.encode() if isinstance(body, str) else body,
            method=verb,
            headers={"Cookie": self.cookie, "X-XSRF-TOKEN": self.xsrf,
                     "X-C4-Tab-Id": self.tab,
                     **({"Content-Type": content_type} if body is not None else {})})
        try:
            with urllib.request.urlopen(req) as r:
                data = r.read()
                return r.status, data
        except urllib.error.HTTPError as e:
            return e.code, e.read()

    def read_file(self, file_url, encoding="utf-8"):
        """Читает текстовый файл через бэкенд (HTTP GET)."""
        st, data = self._http("GET", file_url)
        if st != 200:
            raise RuntimeError(f"read {file_url}: HTTP {st}")
        return data.decode(encoding)

    def write_file(self, file_url, content):
        """Пишет текстовый файл через бэкенд (HTTP PUT). После записи
        для попадания изменений в компилятор нужен rebuild_and_compile()."""
        st, _ = self._http("PUT", file_url, body=content)
        if st not in (200, 201):
            raise RuntimeError(f"write {file_url}: HTTP {st}")
        return True

    # ---------- workspace ----------
    async def add_project(self, proj_url):
        """Добавляет проект в workspace. proj_url — со слэшем на конце!"""
        return await self.call(f"{WORKSPACE}.AddProject", [proj_url])

    async def remove_project(self, proj_url):
        return await self.call(f"{WORKSPACE}.RemoveProject", [proj_url])

    async def open_projects(self):
        r = await self.call(f"{WORKSPACE}.GetOpenProjects", [])
        return r.get("result", [])

    # ---------- объектная модель ----------
    async def tree(self, url, depth=10):
        """Рекурсивно читает дерево объектов. Возвращает dict {path: node}."""
        out = {}
        async def walk(u, d):
            r = await self.call(f"{OBJMODEL}.GetChildNodesAsync", [u])
            nodes = r.get("result") or []
            for n in nodes:
                out[n["path"]] = n
                if not n.get("isLeaf") and d > 0:
                    await walk(n["path"], d - 1)
        await walk(url, depth)
        return out

    async def try_get_node(self, url):
        r = await self.call(f"{OBJMODEL}.TryGetNodeAsync", [url])
        return r.get("result")

    # ---------- сообщения/диагностика ----------
    async def subscribe_messages(self):
        """Подписывается на все пулы сообщений. Возвращает dict cbid->'Pool/Category'."""
        pools = {}
        for pool in ("RunMessagePool", "StatusMessagePool"):
            for cat in ("Build", "Library Resolution", "Compile"):
                cb = self._next_cb()
                pools[cb] = f"{pool}/{cat}"
                await self.call(f"{MSGPOOL}.{pool}.Changes", [cb, cat])
        return pools

    async def collect_messages(self, pools, seconds, on_message=None):
        """Собирает нотификации n секунд. Возвращает список сообщений
        [{severity, message, position, pool}]."""
        found = []
        end = time.time() + seconds
        while time.time() < end:
            try:
                raw = await asyncio.wait_for(
                    self.ws.recv(), timeout=max(0.1, end - time.time()))
            except asyncio.TimeoutError:
                break
            resp = json.loads(raw)
            if resp.get("method") != "_c4-callback/call":
                continue
            cbid = resp["params"][0]
            if len(resp["params"]) < 3 or resp["params"][1] != "onNext":
                continue
            for item in resp["params"][2]:
                if isinstance(item, dict) and item.get("type") == "Add":
                    for m in item.get("added", []):
                        entry = {"pool": pools.get(cbid, cbid),
                                 "severity": m.get("severity"),
                                 "message": m.get("message"),
                                 "position": m.get("position")}
                        found.append(entry)
                        if on_message:
                            on_message(entry)
        return found

    # ---------- компиляция ----------
    async def compile(self, app_url, msg_seconds=45):
        """Компилирует приложение. Возвращает (ok, messages).
        ok = ответ RPC result is True (не гарантирует отсутствие ошибок —
        смотрите messages, severity Error)."""
        pools = await self.subscribe_messages()
        r = await self.call(f"{COMPILER}.Compile", [app_url], timeout=180)
        if "error" in r:
            return False, [{"severity": "RpcError",
                            "message": json.dumps(r["error"], ensure_ascii=False)[:500]}]
        msgs = await self.collect_messages(pools, msg_seconds)
        errors = [m for m in msgs if m["severity"] in ("Error", "RpcError")]
        return not errors, msgs

    async def rebuild_and_compile(self, proj_url, app_url, msg_seconds=90):
        """Надёжная полная сборка: Remove+Add (пересоздание LM с диска) + Compile.
        Подписка на сообщения оформляется ДО пересборки — сборка запускается
        самим AddProject (фоново), и её сообщения тоже перехватываются.
        proj_url — со слэшем. Возвращает (ok, messages)."""
        pools = await self.subscribe_messages()
        await self.remove_project(proj_url)
        await asyncio.sleep(2)
        await self.add_project(proj_url)
        await asyncio.sleep(3)
        r = await self.call(f"{COMPILER}.Compile", [app_url], timeout=180)
        if "error" in r:
            err = {"severity": "RpcError",
                   "message": json.dumps(r["error"], ensure_ascii=False)[:500]}
            return False, [err]
        msgs = await self.collect_messages(pools, msg_seconds)
        errors = [m for m in msgs if m["severity"] in ("Error", "RpcError")]
        return not errors, msgs

    async def restore_libraries(self, app_url):
        r = await self.call(f"{COMPILER}.RestoreMissingLibraries", [app_url])
        return r.get("result")


# ---------- запуск сессии ----------
def _read_capture_url(path, timeout=90):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            txt = open(path, encoding="utf-8").read().strip().strip('"')
            if txt.startswith("http"):
                return txt
        except OSError:
            pass
        time.sleep(2)
    raise TimeoutError("c4-cli не выдал URL (c4capture.cmd/last_url.txt пуст)")


def start_session(project_path):
    """Запускает новую standalone-сессию C4 для проекта.
    Возвращает (C4-объект ещё не подключён, port, cookie, xsrf).
    Дальше: await client.connect() либо использовать c4_connect()."""
    capture_dir = os.path.dirname(_CAPTURE)
    url_file = os.path.join(capture_dir, "last_url.txt")
    if os.path.exists(url_file):
        os.remove(url_file)
    subprocess.Popen(
        ["powershell", "-NoProfile", "-Command",
         f"Start-Process '{_C4_CLI}' -ArgumentList "
         f"'standalone-session','{project_path}','--with-browser','{_CAPTURE}' "
         f"-WindowStyle Minimized"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = _read_capture_url(url_file)
    m = re.match(r"http://localhost:(\d+)/index\.html\?project=([^#]+)#(.+)", url)
    port = int(m.group(1))
    token = m.group(3)
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/UserSessions",
        headers={"InitToken": token})
    with urllib.request.urlopen(req) as r:
        cookie = r.headers["Set-Cookie"].split(";")[0]
        xsrf = r.headers["XSRF-TOKEN"]
    return port, cookie, xsrf


async def c4_connect(project_path):
    """Удобная точка входа: стартует сессию и возвращает подключённого клиента."""
    port, cookie, xsrf = start_session(project_path)
    client = C4(port, cookie, xsrf)
    await client.connect()
    return client


if __name__ == "__main__":
    async def _demo():
        if len(sys.argv) < 2:
            sys.exit("usage: python c4_api.py <project.fbsdev>")
        proj = project_url(sys.argv[1])
        app = proj + "Application.iecapp"
        c = await c4_connect(proj)
        print("подключено, открытые проекты:", await c.open_projects())
        await c.add_project(proj)
        ok, msgs = await c.rebuild_and_compile(proj, app)
        print("compile ok:", ok)
        for m in msgs[:15]:
            print(f"  [{m['severity']}] {m['message'][:160]}")
        await c.close()

    asyncio.run(_demo())
