# Правило 02. Работа с мостом (bridge) и тёплым демоном

Мост — план Б, когда возможностей MCP не хватает, а также основной способ
компиляции и тяжёлых серийных изменений. Всё нижесказанное проверено на этой
машине. Расположение: `CodeSYS-MCP/bridge/`.

### Мост (для операций, которых нет в MCP)

В папке `CodeSYS-MCP/bridge/`: пишешь `task.json` (`{"op": ..., "args": {...}}`),
запускаешь `cmd //c bridge.cmd`, читаешь `result.json`.

* `task.json`/`result.json` — общий ресурс: **перед каждым запуском перезаписывай task.json заново**.
  При параллельных сессиях (несколько агентов) — **обязательно уникальные файлы через env**:
  перед запуском задать `CB_TASK` и `CB_RESULT` (Windows-пути с `\\`), генерировать JSON
  скриптом (python + `json.dump`), не heredoc'ом.
* Полезные op: `build` (компиляция; `args.application` = `"<Устройство>/Plc Logic/Application"`),
  `batch` (много шагов create/set_code за один запуск CODESYS — используй всегда для серий изменений),
  `dump_tree` (рекурсивный дамп текста объектов), `tree` (рекурсивный дамп имён/GUID типов,
  `args.path` + `args.max_depth`), `get_object` (чтение объекта, включая textual_declaration),
  `eval` (выражение Python в контексте ScriptEngine: доступны `proj`, `find_obj`, `tree`,
  `projects` — через него вызываются методы-расширителей: `export_native`, `import_native`,
  `create_folder`, `GetType().GetMethods()` и т.п.),
  `ensure_task`, `create_interface`,
  `add_device`, `create_project`,
  `validate_library` (обязателен после любого изменения библиотеки: компилирует
  `Kimi_Lib.library` напрямую, `args.library` = путь к `.library`; `args.project`
  не обязателен — если задан и файл существует, выполняется ещё и инкрементальный
  синк в проект-зеркало, если нет/удалён — валидация библиотеки standalone),
  `delete_object` (удаление объекта; **только по явной команде пользователя** — см. «Библиотека»).
* Критерий успеха сборки — строка «Компиляция завершена -- 0 ошибок» в messages.
  Внимание: поле `build_result` (`bool(res)` из `app.build()`) на этой версии недостоятельно —
  ориентируйся на текст messages.

### Тёплый демон (ускорение ~20×, проверено 2026-09-19)

Каждый запуск моста/MCP = новый процесс CODESYS (~20–90 с на запуск+открытие проекта;
сама операция — <1–3 с). Для серийной работы есть **демон**: один `--noUI`-процесс живёт
вечно и исполняет задачи из очереди в тёплой сессии (проект остаётся открытым, save после
каждой задачи).

* **Первый шаг любой рабочей сессии агента** — проверить пульс (`python bridge_client.py ping`)
  и, если демон мёртв, стартовать его (проект в GUI при этом закрыт):
  `powershell -NoProfile -Command "Start-Process -FilePath '...\\bridge_daemon.cmd' -WindowStyle Minimized"`,
  затем `python bridge_client.py wait`. Загрузка ~2–25 с, дальше — горячо. MCP после перезапуска
  своего stdio-процесса ходит через демон сам (см. ниже).
* Задача: кладём `{"op": ..., "args": {...}}` в `bridge/queue/<id>.json` —
  удобнее через клиента: `python bridge_client.py submit <task.json> [--timeout 240]`
  (печатает result и замер `elapsed_s`); задачи с `keep_open` не нужны — демон сам
  держит проект открытым (можно переопределить `args.keep_open=false`).
* Контроль: `python bridge_client.py ping` (живость, аптайм, открытые проекты),
  `python bridge_client.py stop` (save + close всех проектов + выход),
  `python bridge_client.py wait` (дождаться загрузки после старта).
* Замеры на Project_One: get_object 1.4 с, tree 0.8 с, build 13 с (компиляция SoftMotion
  тяжёлая сама по себе) — против 23–29 с разового запуска на любую операцию.
* **Правило владения:** пока демон держит проект открытым, GUI CODESYS и MCP-мост к
  этому проекту его открыть не смогут. Рабочий цикл: стартуешь демон → работаешь через
  него → `stop` перед ручной работой в GUI. Разовый мост и MCP остаются fallback'ом,
  когда демон не запущен.
* Демон сам закрывает проекты после 15 мин без задач (блокировки файлов снимаются),
  процесс при этом живёт; каталог очереди — `bridge/queue/`, пульс — `daemon_ping.json`,
  журнал загрузки — `daemon_boot.log`. Диагностика зависания — `bridge_smoke.cmd`
  (heartbeat-тест жизнеспособности `--noUI`-процесса).
* Скрипты демона пишутся **без py3--only API** (ScriptEngine — python2-совместимый:
  никаких `os.replace`, `makedirs(exist_ok=...)`, f-строк).
* **Warm-up при старте** (список — `bridge/warm_projects.txt`, один путь на строку;
  перекрывается env `CB_WARM_PROJECTS` через `;`): демон заранее открывает частые проекты.
  Важно: warm-проекты открываются **`primary=False`** — иначе валидация библиотеки в тёплой
  сессии зависает навсегда на `create_property` (проверено: primary занят warm-проектом →
  структурные правки в проекте-зеркале висят; с `primary=False` всё проходит за ~20 с).
  primary-слот остаётся свободным для задачи, которая приходит в очередь.
* **`app.build()` в ScriptEngine всегда возвращает None** — вердикт о сборке брать из
  сводки компилятора («…-- N ошибок, M предупреждений», локализована). Мост сам парсит её:
  `build_result` (True при N=0) и новое поле `warnings` в ответах `validate_library`/`build`.
  Детали ошибок: `system.get_message_objects(<guid категории "Компиляция">)` — у объектов
  есть `.text`, `.position_text`, `.object.get_name()` (привязка к объекту/строке).
* **Инкрементальная `validate_library`** (2026-09-20): в режиме с зеркалом сравнивает
  объекты библиотеки с состоянием зеркала (sidecar-манифест `bridge/mirror_manifest_<md5>.json`,
  дети сортируются — порядок членов у CODESYS плавает), копирует только изменившиеся
  (+ implementors и `POINTER TO`-ссыльщики изменённого интерфейса). **С 2026-09-20 зеркало
  упразднено** — рабочий режим standalone: только `check_all_pool_objects()` по самой
  `.library`, ~5–8 с, ответы: `build_result/warnings/error_count/check/messages`.
* **Проверка библиотеки — `check_all_pool_objects()`** (script API команды GUI
  «Build → Check all Pool Objects», F11 для `.library`): работает ТОЛЬКО на primary-проекте
  и ТОЛЬКО на `.library`. Это тот же library-контекст, что в IDE (0/0), без шума
  визуализации/устройства зеркального приложения. Поэтому `validate_library` переводит
  библиотеку в primary (warm-копию закрывает/переоткрывает, зеркало при необходимости
  демоутит в secondary) и ПОСЛЕ проверки восстанавливает warm-состояние (secondary) —
  чужой primary в тёплой сессии вешает структурные правки. Сборка приложения зеркала
  как критерий НЕ используется: она даёт сотни ложных ошибок (визуализация
  «Относительная позиция», неоднозначность имён в project-контексте), которых в
  library-контексте нет.
* **Сообщения компилятора**: категории перечислять динамически
  (`system.get_message_categories()`), перед сборкой чистить (`system.clear_messages`),
  severity сравнивать декодированной строкой (`str(m.severity)` — 'Error'/'Warning'/
  'FatalError'; битовая маска Severity across versions ненадёжна), у объектов сообщений
  есть `.text/.prefix+.number/.object.get_name()/.position_text`.
  Заимствовано из `Example_MCP/luke-harrimanCodesys-MCP` и `zbest1000mcptoolkit-for-codesys`.
* После `taskkill //F` по процессу CODESYS рядом с проектом остаётся файл `*.~u` —
  удали его перед следующим открытием, иначе «проект занят».
* **MCP-сервер умеет в демон сам**: `src/mcp/bridge.ts` проверяет пульс `daemon_ping.json`
  и, пока демон жив, шлёт задачи в `bridge/queue/` (~1–3 с на вызов), иначе — старый
  spawn (~20–90 с). Пинг со `status: "stopped"` считается мёртвым (cold fallback).
  **Автостарт**: если демона нет, MCP сам стартует его и ждёт пульс (первый вызов сессии
  платит ~20–30 с, дальше горячо); отключить — env `CODESYS_BRIDGE_AUTOSTART=0`.
  Тонкость: stdio-процесс MCP должен перезапуститься, чтобы подхватить новый код —
  маршрутизация действует с новой сессии. End-to-end тест — `node test-daemon-route.mjs`
  (демон остановлен: ожидается `daemonAlive before: false` → автостарт → `ok: true`).
* **`get_object`/`list_objects`/`tree`/`obj_info` принимают `slim: true`** — children
  отдаются именами (name+type) вместо полного дампа: 109 объектов Project_One — копеечный
  ответ вместо мегабайтного. По умолчанию (без slim) поведение прежнее.

## Окно-монитор демона (2026-10-27)

`bridge_daemon.cmd` теперь стартует **безголово и отсоединённо** (через WMI в
`bridge_daemon.ps1`): нет консольного окна, которое можно случайно закрыть
(закрытие консоли убивало CODESYS-процесс демона), процессы переживают смерть
запустившего их. Рядом поднимается tkinter-окно **`daemon_monitor.pyw`**
(секундный опрос `daemon_ping.json`/очереди/`daemon_boot.log`): статус
(жив/ошибка цикла/остановлен), pid, аптайм, список открытых проектов
(первый = primary), очередь задач с именем проекта «в работе», хвост лога.
Закрытие окна демон НЕ останавливает; при штатном стопе демона окно
закрывается само. Отключить окно: `CB_MONITOR=0` перед запуском cmd.
Держать ровно один демон: ps1 сам убивает существующие CODESYS.exe
(отключить: `CB_KEEP=1`).

## Реестр операций (ops) моста

Чтение объектов/дерева: `get_object`, `list_objects`, `tree`, `dump_tree`,
`project_info`, `reflect`, `eval` (только выражения — без присваиваний;
для сложного — `lambda`; глобалы ScriptEngine: `proj, projects, system,
librarymanager, find_obj, tree, get_project`).

Изменения: `create_pou`, `create_interface`, `create_member`, `create_dut`,
`create_gvl`, `set_code`, `delete_object` (только по явной команде
пользователя), `ensure_task`, `add_device`, `save_project`, `close_project`,
`open_project`, `create_project`, `list_open_projects`.

Серии изменений — всегда одним `batch` (сохраняет проект в конце; каждый
запуск моста = новый экземпляр CODESYS, несохранённое теряется).

Сборка и библиотеки:
- `build` — `app.build()` требует PRIMARY-проект; warm-secondary мост
  временно промоутит и вернёт обратно. Критерий успеха — «0 ошибок».
- `validate_library` — **standalone**: `args.project` не нужен; делает
  pool-check библиотеки напрямую (~7 с). Зеркало-проект не используется.
- `lib_install` — установка библиотеки в репозиторий:
  `librarymanager.install_library(path, repo, overwrite)`; **repo передавать
  всегда явно** (одноаргументный вызов падает с ArgumentNullException).
- `lib_add` / `lib_remove` / `lib_list` — ссылками в Library Manager проекта;
  `lib_add` ищет библиотеку через `find_library` (полный display name!) с
  fallback-перебором по префиксу.
- `add_file` — подключение внешнего файла (MD-документация и пр.) к корню
  проекта/устройству/application: `create_external_file_object`; режимы
  `link` (по умолчанию, файл живёт на диске), `embed`, `link_and_embed`.

## Железные правила моста

1. Ровно ОДИН демон CODESYS. Перед стартом — убить все процессы и удалить
   `*.~u` lock-файлы рядом с проектами. Несколько демонов = драка за очередь
   и «мистические» падения (поймано при 7 процессах).
2. Warm-проекты открываются с `primary=False` — иначе create_property и
   часть операций зависают/падают.
3. После правки `bridge.py` демон надо перезапустить (ops кэшируются).
4. Паттерн вызова: писать task-JSON скриптом → `python bridge_client.py
   submit <file> --timeout N` → удалить временный файл. В параллельных
   сессиях — уникальные имена через `CB_TASK`/`CB_RESULT`.
   Для накопления датасета (`Library/_dataset/`) вместо прямого submit —
   `python Library/_dataset/collect.py submit <file> --timeout N`: архивирует
   task+result в `bridge_log/` и пишет сводку; демон не трогает.
