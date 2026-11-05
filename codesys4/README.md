# CODESYS 4 — headless-инструменты

Результаты практического исследования CODESYS 4 (2026-10-30): как собирать
проекты без GUI и как общаться с внутренним JSON-RPC API. Всё проверено
экспериментально на одной машине — недокументированный API может измениться
в любой версии.

## Архитектура CODESYS 4 (как мы её поняли)

CODESYS 4 — локальный ASP.NET-бэкенд (`c4-cli.exe` / `CODESYS-4.exe`, порт
`127.0.0.1:5xxxx` на сессию) + веб-фронт. Проект на диске — папка `*.fbsdev/`
с текстовыми файлами: `Application.iecapp^/` (`*.prg.st`, `*.gvl`,
`Libraries.json`, `TaskConfiguration.json`), `Devices/DeviceTree.json`.

**Главный принцип: основной путь — headless через `c4-cli`, без GUI и без
сессий.** JSON-RPC/WS-интерфейс существует, но компилятор по RPC не
инвалидирует свой кэш language model от внешних правок файлов — сборку по RPC
запустить не удалось. `bootapp compile` всегда собирает с диска.

Рабочий цикл агента:
1. Правим файлы проекта напрямую (текст `*.prg.st` / `*.gvl` / json).
2. `python c4_build.py <проект.fbsdev>` — сборка + разбор диагностики.
3. Ошибки получаем объектами `Diag` (severity, message, path, line, col).

## Файлы

| Файл | Назначение |
|---|---|
| `c4_build.py` | Headless-сборка: `compile_app()`, `C4Project`, `parse_diagnostics()`. Путь к c4-cli — env `C4_CLI` |
| `c4_api.py` | Обвязка сессий: `c4_connect()`, класс `C4` (WS + HTTP-файлы + пулы сообщений компиляции) |
| `c4_client.py` | Низкоуровневый WS-клиент + примеры вызовов (учётка сессии через env/argv) |
| `c4proxy.py` | Локальный WS-прокси для перехвата трафика фронта (парсинг WS-фреймов, лог `proxy_traffic.log`) |
| `get_c4_session.py` | Достаёт сессионную cookie из профиля WebView2 (DPAPI + AES-GCM; нужен `pip install cryptography`) |
| `c4capture.cmd` | Заглушка-браузер: перехватывает URL с одноразовым InitToken, не открывая окно (пишет в `last_url.txt`) |
| `c4browser.cmd` | Запуск Chrome через прокси c4proxy (для самостоятельного перехвата) |
| `rpc_methods.txt`, `rpc_catalog.txt` | Каталог обнаруженных JSON-RPC-методов с сигнатурами |
| `full_cycle_out.txt` | Эталонный прогон полного цикла: AddProject → подписки на пулы сообщений → Compile → диагностика |

## Быстрый старт

```bash
pip install websockets          # c4_api.py / c4_client.py
pip install cryptography        # get_c4_session.py

# 1. Headless-сборка (основной сценарий)
set C4_CLI=C:\path\to\c4-cli.exe
python c4_build.py C:\path\to\project.fbsdev

# 2. Сессия + RPC (онлайн-операции по контроллеру, живое дерево объектов)
python -c "import asyncio, c4_api; asyncio.run(c4_api.c4_connect(r'C:\path\to\project.fbsdev'))"
```

## Грабли (кратко)

- URL проекта в `AddProject` обязан кончаться на `/` (`file:///.../proj.fbsdev/`).
- `Compile` по RPC возвращает `true`, даже когда ничего не собрал (кэш LM).
- HTTP POST на `/api/JsonRpc` не работает (400) — только WebSocket.
- Файлы читаются/пишутся НЕ через JSON-RPC: `GET/PUT /api/FileSystemHttp?fileUrl=…`
  с заголовками Cookie, X-XSRF-TOKEN, X-C4-Tab-Id.
- Тестовые standalone-сессии копятся в фоне — проверять `tasklist | findstr c4-cli`.

Полный список — в [docs/10-codesys4.md](../docs/10-codesys4.md).
