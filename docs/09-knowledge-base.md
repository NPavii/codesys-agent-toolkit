# Правило 09. База знаний: что где искать

Карта источников решений. Порядок перебора — в `Rules/01-workflow.md`.

## Свои источники

| Что | Где | Как искать |
|---|---|---|
| Проверенные решения | `Kimi_Lib` → `Library/README.md` (источник истины — сам `.library`) | Состав и паттерны — в README |
| Идеи/паттерны эталонного проекта | `Rules/08-machinelib.md` | Полный список DUT/FB/PRG MachineLib |
| Грабли этой машины | `Rules/06-pitfalls.md` | Читать перед незнакомой операцией |
| ScriptEngine API | `CodeSYS-MCP/bridge/bridge.py` (реестр OPS + eval-контекст: `proj, projects, system, librarymanager, find_obj, tree`) | grep по имени op/метода; штатного `scriptDoc.txt` в воркспейсе нет (каталог `Example_MCP/` отсутствует — ссылки на него в AGENTS.md устарели) |
| Визуализация / WebVisu / Library Manager (объекты без текстового API) | `native_export` → правка archivable-XML → `native_import` (замещение = `delete_object` + `rename_object`, import всегда даёт копию `X_1`) | датасет `2026-10-012`, грабли `Rules/06` (2026-10-30), генератор `Project/ANK101/_gen_panel.py` |
| Нормативные документы и мануалы | `CODESYS_Knowledge_Base/08_Documentation_and_Manuals/` (PackML Implementation Guides, OMAC OEE Guide, OMAC whitepaper + реестр в `README.md`) | Читать по месту; PDF — справочно |

## Установленные библиотеки (системный репозиторий)

`C:\ProgramData\CODESYS\Managed Libraries` — общий список виден в выводе
`ping` моста (open_projects) и в Library Manager:

- **Standard** 3.5.18.0 — таймеры (TON/TOF/TP/R_TRIG/F_TRIG), строки,
  триггеры; **Util** — доп. FB (симуляторы, границы, стеки/очереди);
  **Standard64**, **Collections** (+interfaces), **StringUtils**,
  **FloatingPointUtils**.
- **OSCAT** — см. `Rules/05` (проверять наличие версии в репозитории
  перед использованием).
- **SM3_*** (SoftMotion: basic, rbase, ramps, math, CNC, robotics,
  transformation...) — движение/позиционирование.
- **Visu*/CmpVisu*** — визуализация; **AlarmManager** + **visuelemsalarm** —
  аварии; **Datasources** — OPC/данные.
- **CAA** (file, storage, tick, async manager...) — файлы/часы/асинхрон.
- Вендорские: Leadshine (mc_hsio, mc_syslib, ls_basicmodule), Optimus Drive
  (od_basic), Stoik (target id checks).

## Как проверить состав незнакомой библиотеки

- Текстовые `.library` — открыть через мост (`open_project` + `dump_tree`/
  `tree`) и читать как обычный проект.
- Компилированные `.compiled-library` — интроспекция через ScriptEngine
  ограничена; практичный путь: подключить в тестовый проект через
  `lib_add` и смотреть дерево (`dump_tree`), либо смотреть в GUI
  Library Manager. Не выдумывать состав по памяти.
