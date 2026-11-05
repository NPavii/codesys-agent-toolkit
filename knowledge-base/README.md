# CODESYS Knowledge Base

Многоуровневая база знаний по экосистеме CODESYS для использования AI-агентами
при написании программ (IEC 61131-3 / ST). Миссия и требования — в брифе
«# РОЛЬ» (сессия 2026-09-21).

Статусы: ✅ наполнен · 🚧 черновик · ⬜ исследование предстоит.

## Оглавление

| # | Раздел | Статус | Содержание |
|---|---|---|---|
| 1 | [01_Projects_and_Templates](01_Projects_and_Templates/) | ✅ | `github_projects.md` — локально изученные (14) + веб-обход GitHub (awesome-списки, утилиты, motion) |
| 2 | [02_Libraries](02_Libraries/) | ✅ | `standard_libraries.md` (встроенные, OSCAT с CVE, coUnit, community) + `mqtt_library.md` (вердикт FieldFox) |
| 3 | [03_AI_Prompts_and_MCP](03_AI_Prompts_and_MCP/) | 🚧 | `mcp_servers_comparison.md` — 11 серверов (3 локально + веб-карта). Дальше: промпты, setup-гайды |
| 4 | [04_Addons_and_Tools](04_Addons_and_Tools/) | ✅ | `professional_developer_edition.md` (PDE €550/год, состав, официальный MCP) + `free_tools.md` |
| 5 | [05_Best_Practices](05_Best_Practices/) | 🚧 | `oop_patterns.md` (7 паттернов), `state_machine_patterns.md` (PackML), `testing_strategies.md` (coUnit). Дальше: naming, error handling, arrays |
| 6 | [06_Modern_Requirements](06_Modern_Requirements/) | 🚧 | `security_iec62443.md`. Дальше: OPC UA/MQTT IIoT, digital twin, AI-engineering |
| 7 | [07_Manufacturer_Specific](07_Manufacturer_Specific/) | ✅ | `platforms_overview.md` — WAGO/PLCnext/Schneider/Festo/ctrlX/ifm/Pilz/TwinCAT + грабли переноса |
| 8 | [08_Documentation_and_Manuals](08_Documentation_and_Manuals/) | ✅ | `codesys_online_help_links.md` — офиц. ресурсы, курсы, FAQ |

## Как пользоваться (для AI-агента)

* Задачи «как спроектировать машину/модуль/автомат» → `05_Best_Practices/state_machine_patterns.md`
  + карта эталонных репозиториев: `01_Projects_and_Templates/github_projects.md`.
* Задачи «ООП в ST: интерфейсы/наследование/паттерн» → `05_Best_Practices/oop_patterns.md`.
* Задачи «подключить протокол/библиотеку» → `02_Libraries/*` (проверяй версию CODESYS!).
* Задачи «автоматизировать IDE» → `03_AI_Prompts_and_MCP/mcp_servers_comparison.md`;
  рабочие регламенты моста — в `../docs/02-bridge.md` (не дублировать здесь).
* Эталонные проекты (PackML-бандл, SPT, TwinCAT-примеры) изучены локально —
  только выводы, клоны в репозиторий не включены.

## Сводка ресурсов (по состоянию 2026-09-21, конец веб-обхода)

| Тип | Количество | Где |
|---|---|---|
| Репозиториев изучено локально | 14 | PackML-бандл (11), Applied-Design-Patterns-in-CODESYS-V3, Codesys-Mqtt-lib, плюс 3 MCP-сервера (локально, клоны не включены) |
| MCP-серверов сравнено | 11 | `03_AI_Prompts_and_MCP/mcp_servers_comparison.md` |
| Библиотек/утилит охвачено | ~20 | `02_Libraries/standard_libraries.md`, `free_tools.md` |
| Паттернов разобрано | 7 | `05_Best_Practices/oop_patterns.md` |
| Платформ-производителей | 9 | `07_Manufacturer_Specific/platforms_overview.md` |
| Промптов | 0 | ⬜ БЛОК 3, следующая итерация |

План: дальнейшие блоки (промпты, setup-гайды MCP, naming/error-handling,
OPC UA/MQTT IIoT-практика, digital twin) наполняются точечными исследованиями;
верификация версий и цен — перед боевым использованием.
