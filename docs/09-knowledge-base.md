# Правило 09. База знаний: что где искать

Карта источников решений. Порядок перебора — в `docs/01-workflow.md`.
Пути к рабочим проектам и своей библиотеке пользователь задаёт при настройке
области (см. `docs/01-workflow.md` → «Своя область»).

## Свои источники

| Что | Где | Как искать |
|---|---|---|
| Проверенные решения | своя библиотека решений (если настроена; дизайн — `library/README.md`) | Состав и паттерны — в README библиотеки |
| Идеи/паттерны эталонной библиотеки | `docs/08-machinelib.md` | Полный список DUT/FB MachineLib |
| Грабли | `docs/06-pitfalls.md` | Читать перед незнакомой операцией |
| ScriptEngine API | `bridge.py` моста MCP-сервера (реестр OPS + eval-контекст: `proj, projects, system, librarymanager, find_obj, tree`) — [codesys-mcp-server](https://github.com/NPavii/codesys-mcp-server) | grep по имени op/метода |
| Визуализация / WebVisu / Library Manager (объекты без текстового API) | `native_export` → правка archivable-XML → `native_import` (замещение = `delete_object` + `rename_object`, import всегда даёт копию `X_1`) | датасет `2026-10-012`, грабли `docs/06` (2026-10-30) |
| Нормативные документы и мануалы | `knowledge-base/08_Documentation_and_Manuals/` + официальный сайт CODESYS | Читать по месту; PDF — справочно |

## Установленные библиотеки (системный репозиторий)

`C:\ProgramData\CODESYS\Managed Libraries` — общий список виден в выводе
`ping` моста (open_projects) и в Library Manager:

- **Standard** 3.5.18.0 — таймеры (TON/TOF/TP/R_TRIG/F_TRIG), строки,
  триггеры; **Util** — доп. FB (симуляторы, границы, стеки/очереди);
  **Standard64**, **Collections** (+interfaces), **StringUtils**,
  **FloatingPointUtils**.
- **OSCAT** — см. `docs/05-external-libs.md` (проверять наличие версии в
  репозитории перед использованием).
- **SM3_*** (SoftMotion: basic, rbase, ramps, math, CNC, robotics,
  transformation...) — движение/позиционирование.
- **Visu*/CmpVisu*** — визуализация; **AlarmManager** + **visuelemsalarm** —
  аварии; **Datasources** — OPC/данные.
- **CAA** (file, storage, tick, async manager...) — файлы/часы/асинхрон.
- Вендорские библиотеки производителей оборудования — проверять состав
  через Library Manager или `tree` моста, не выдумывать по памяти.

## Как проверить состав незнакомой библиотеки

- Текстовые `.library` — открыть через мост (`open_project` + `dump_tree`/
  `tree`) и читать как обычный проект.
- Компилированные `.compiled-library` — интроспекция через ScriptEngine
  ограничена; практичный путь: подключить в тестовый проект через
  `lib_add` и смотреть дерево (`dump_tree`), либо смотреть в GUI
  Library Manager. Не выдумывать состав по памяти.
