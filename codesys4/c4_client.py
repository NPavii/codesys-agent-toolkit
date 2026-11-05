# -*- coding: utf-8 -*-
"""Полноценный RPC-клиент для CODESYS 4 + тесты методов.

Учётные данные сессии (одноразовые, живут ~пока жива сессия c4-cli):
  python c4_client.py <port> <cookie> <xsrf>
или env C4_PORT / C4_COOKIE / C4_XSRF (см. get_c4_session.py / c4_api.py).
"""
import asyncio, json, uuid, sys, os
import websockets

PORT = int(os.environ.get("C4_PORT", "0"))
COOKIE = os.environ.get("C4_COOKIE", "")
XSRF = os.environ.get("C4_XSRF", "")
if not PORT and len(sys.argv) > 3:
    PORT, COOKIE, XSRF = int(sys.argv[1]), sys.argv[2], sys.argv[3]
if not (PORT and COOKIE and XSRF):
    sys.exit("задайте C4_PORT/C4_COOKIE/C4_XSRF или передайте <port> <cookie> <xsrf>")

class C4Client:
    def __init__(self, port, cookie, xsrf):
        self.url = f"ws://127.0.0.1:{port}/api/JsonRpc"
        self.cookie = cookie
        self.xsrf = xsrf
        self.tab = str(uuid.uuid4())
        self.ws = None
        self._id = 0

    async def connect(self):
        headers = {
            "Cookie": self.cookie,
            "Origin": f"http://127.0.0.1:{self.url.split(':')[2].split('/')[0]}",
            "X-XSRF-TOKEN": self.xsrf,
            "X-C4-Tab-Id": self.tab,
        }
        self.ws = await websockets.connect(
            self.url, subprotocols=[f"tab.{self.tab}"],
            additional_headers=headers, max_size=100_000_000)
        return self

    async def call(self, method, params=None, timeout=15):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        await self.ws.send(json.dumps(msg))
        # пропускаем уведомления без id
        while True:
            raw = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            resp = json.loads(raw)
            if resp.get("id") == self._id:
                return resp
            # иначе это нотификация — покажем кратко
            print(f"  [notify] {str(resp)[:4000]}")

    async def close(self):
        if self.ws: await self.ws.close()

async def main():
    c = await C4Client(PORT, COOKIE, XSRF).connect()
    print("=== подключено ===")
    tests = [
        ("CODESYS.C4.Modules.Bootstrapping.HostEnvInfo.GetHostEnvInformation", []),
        ("CODESYS.C4.Modules.WorkspaceManager.GetOpenProjects", []),
        ("CODESYS.C4.Modules.WorkspaceManager.GetOpenWorkspaceFile", []),
        ("CODESYS.C4.Sdk.FileSystem.IFileSystem.GetRoots", []),
    ]
    for method, params in tests:
        print(f"\n>>> {method}")
        try:
            r = await c.call(method, params)
            print(json.dumps(r, ensure_ascii=False, indent=1)[:1500])
        except Exception as e:
            print("ERR:", e)
    await c.close()

if __name__ == "__main__":
    asyncio.run(main())
