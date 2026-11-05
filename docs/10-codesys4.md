# Правило 10. Работа с CODESYS 4 (headless + сессии)

CODESYS 4 — это локальный ASP.NET-бэкенд (`c4-cli.exe` / `CODESYS-4.exe`,
порт 127.0.0.1:5xxxx на сессию) + веб-фронт. Проект на диске — папка
`*.fbsdev/` с текстовыми файлами: `Application.iecapp^/` (реальное
содержимое: `*.prg.st`, `*.gvl`, `Libraries.json`, `TaskConfiguration.json`),
`Devices/DeviceTree.json`. Всё проверено на этой машине (2026-10-30).

## Главный принцип

**Основной путь — headless через `c4-cli`, без GUI и без сессий.**
JSON-RPC/WS-интерфейс существует (см. ниже), но компилятор по RPC не
инвалидирует свой кэш language model от внешних правок файлов — сборку
запустить нельзя. `bootapp compile` всегда собирает с диска.

Рабочий цикл агента:
1. Правим файлы проекта напрямую (текст `*.prg.st` / `*.gvl` / json).
2. `python c4probe/c4_build.py <проект.fbsdev>` — сборка + разбор диагностики.
3. Ошибки получаем объектами `Diag` (severity, message, path, line, col).

## Headless-сборка (c4probe/c4_build.py)

* `c4-cli bootapp compile <Application.iecapp> [target]` — полная офлайн-сборка.
  **exit code 0 = успех**; иначе ошибки с позициями `(строка, колонка, length)` в stdout.
  Вывод локализован (рус/eng) — парсер в модуле переваривает оба.
* По умолчанию результат в темповую папку (проект не пишется). Стандартное
  место GUI — `<Application.iecapp^>/.bootapp/`.
* `c4-cli library set-managed/set-relative/set-placeholder …` — работа с Libraries.json.
* `c4-cli librepo …` — репозитории библиотек.
* Вызов c4-cli занимает ~5–15 с (подъём рантайма на каждый вызов) — серии
  правок объединять в один проход, компиляцию дёргать один раз в конце.
* Разбор вывода: длинные пути c4-cli рвёт по строкам — парсер склеивает
  обратно по факту существования файла (`c4_build.parse_diagnostics`).

## API сессий (c4probe/c4_api.py) — только если headless не хватает

Нужно для: онлайн-операций по контроллеру (Login/Start/Stop/Reset через
`IOnlineAppService`), живого дерева объектов, наблюдения за сообщениями.
Не нужно для: правки кода и компиляции.

Транспорт и авторизация (всё уже в `c4_api.py`):
* Запуск: `c4-cli standalone-session <проект.fbsdev> --with-browser c4capture.cmd`
  (c4capture пишет URL с одноразовым InitToken в `c4probe/last_url.txt`, браузер не открывает).
* Обмен: `curl -H "InitToken: <token>" http://127.0.0.1:<port>/api/UserSessions`
  → cookie `codesys_4_auth` + заголовок `XSRF-TOKEN`. Токен одноразовый.
* RPC: WebSocket `ws://127.0.0.1:<port>/api/JsonRpc`, сабпротокол `tab.<uuid>`,
  заголовки `Cookie`, `X-XSRF-TOKEN`, `X-C4-Tab-Id`, `Origin`.
* Файлы (НЕ JSON-RPC!): `GET/PUT /api/FileSystemHttp?fileUrl=<url>` с теми же
  заголовками. Без `X-C4-Tab-Id`/`XSRF` — 400 «Invalid XSRF token».
* Диагностика: подписки `CODESYS.C4.Modules.MessagePool.{Run,Status}MessagePool.Changes`
  с параметрами `[callbackId, category]`; категории: Build, Library Resolution, Compile;
  события приходят методом `_c4-callback/call` с `onNext [{type: Add|Clear, added: [...]}]`.
  **Пулы накапливаются за сессию и реплеят состояние при подписке.**

## Грабли CODESYS 4 (проверено на этой машине)

* **URL проекта в `AddProject` обязан кончаться на `/`** (`file:///.../proj.fbsdev/`).
  Без слэша `WorkspaceMetaManager` падает («Path is outside a project»), а `Compile`
  таймаутится 120 с («did not become available in the workspace»).
* `Compile` по RPC возвращает `true`, даже когда ничего не собрал (кэш LM).
  Реальную сборку по RPC запустить не удалось — поэтому headless через bootapp.
* `RemoveProject` удаляет `.library-cache` внутри проекта; следующий `AddProject`
  сам подтягивает библиотеки из extension-пакетов (быстро, офлайн).
* PUT файла через FileSystemHttp сам по себе компилятор не будит; вотчер
  (`IFileSystemWatcher.WatchEntry`) события шлёт, но LM это не инвалидирует.
* HTTP POST на `/api/JsonRpc` не работает (400) — только WebSocket.
* Chrome не проксирует `localhost` (обходится только с `--proxy-bypass-list="<-loopback>"`
  на чистом профиле; `<-loopback>` PowerShell может съесть) — для перехвата трафика
  проще слушать порты, чем мучить прокси.
* GUI CODESYS 4 и сессии `c4-cli` — разные процессы; тестовые standalone-сессии
  копятся в фоне, проверять `tasklist | findstr c4-cli` и прибивать лишние.
* CODESYS V3 MCP (`codesys-mcp`) к C4 неприменим — таймаут, не использовать.

## Карта файлов

* `c4probe/c4_build.py` — headless: `compile_app()`, `C4Project`, `parse_diagnostics()`.
* `c4probe/c4_api.py` — сессии: `c4_connect()`, `C4` (WS + HTTP-файлы + пулы сообщений).
* `c4probe/c4_client.py` — низкоуровневый WS-клиент (тесты, прототипы).
* `c4probe/c4capture.cmd` — перехват InitToken без открытия браузера.
* Справка c4-cli: `c4-cli --help`, `c4-cli bootapp compile --help`.
