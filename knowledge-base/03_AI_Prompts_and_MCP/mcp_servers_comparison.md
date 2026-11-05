# MCP-серверы для CODESYS: сравнение

Дата среза: 2026-09-21. Три сервера изучены по локальным копиям в
`Example_MCP/` (только чтение) — это реальные исходники, а не описания из сети.
Четвёртый столбец — наш рабочий плагин (производное от luke-harriman и
zbest1000, см. `Rules/02-bridge.md`).

## Сравнительная таблица

| | @codesys/mcp-toolkit (johannesPettersson80) | codesys-mcp-persistent (luke-harriman) | mcptoolkit-for-codesys (zbest1000) | codesys-mcp (наш плагин) |
|---|---|---|---|---|
| Язык | TypeScript (Node ≥18) | TypeScript (Node 18+) | Python ≥3.11 | TypeScript + Python-bridge |
| CODESYS | 3.5 SP21 (scripting) | SP19/SP20 persistent; **SP21+ только headless** | 3.5 **SP22** (заявлено и проверено), должно работать SP19+ | 3.5.21.x (рабочий профиль воркспейса) |
| Инструментов | ~10 (project/POU/property/method/compile) + 3 ресурса | **41 инструмент** + 3 ресурса | **82 инструмента** | ~50 инструментов (MCP-объявлено) + ~30 ops моста |
| Режим | headless на вызов (spawn CODESYS) | persistent (CODESYS UI открыт, IPC-watcher внутри IDE) | persistent-стиль с защитой от модальных диалогов; live-тесты против soft-PLC | **тёплый демон** (`--noUI` процесс живёт между вызовами, очередь задач) |
| Онлайн-операции (PLC) | нет | ограниченно | **да**: login/logout, read/write/force переменных | да: online_login/read/write/force/status |
| Библиотеки | нет | нет | add/remove/diagnose | lib_add/remove/list/install + `validate_library` (pool-check .library) |
| Сборка | compile_project | есть | build + lint-отчёт `build.validate` | build + парсинг «0 ошибок/предупреждений» |
| Устройства | нет | нет | поиск по репозиторию 3000+ устройств, add, update pins | add_device |
| Тесты | — | vitest | 199 unit + 6 live integration | smoke-тест демона |
| Лицензия | MIT (npm-пакет) | см. репозиторий | MIT-стиль (см. LICENSE) | локальный плагин |

## Выводы

1. **luke-harriman**: уникален persistent-режимом (видно в IDE в реальном
   времени), но на SP21+ падает в headless — для нас не критично, т.к. GUI во
   время работы агента закрыт (`Rules/02`).
2. **zbest1000**: самый широкий охват (82 инструмента: device repository,
   task config, PLCopenXML, mirror-export под git, онлайн-цикл) — основной
   донор функций для нашего плагина.
3. **johannesPettersson**: минимальный, удобен как учебный пример архитектуры;
   опубликован в npm как `@codesys/mcp-toolkit`.
4. Наш плагин расширен **тёплым демоном** (один процесс CODESYS на сессию,
   ~20× быстрее серийных операций) и standalone-валидацией `.library` —
   этого нет ни в одном из трёх исходников.

## Веб-обход 2026-09-21: расширенная карта MCP-экосистемы

| Сервер | Автор | Инструменты | Особенности |
|---|---|---|---|
| **Codesys-MCP-SP21-plus** | phobicdotno (Karstein Kvistad) | ~50+ | Форк luke-harriman с watcher-переписью под **SP21+/SP22** (`execute_on_primary_thread` убрали в SP21); version-anchor, release pipeline; live-верификации на SP22 Patch 1 |
| **PhilipLykov/Codesys-MCP-Server** | PhilipLykov | **113** | Производное от phobicdotno: restricted online-control workflow, verification gates, оркестрация Static Analysis, DPAPI-хранилище учёток PLC/проектов |
| **ab-mcp-toolkit** (codesys-mcp-persistent) | babos1908 | **75** | Дроп-ин замена @codesys/mcp-toolkit (тот — строгое подмножество); +online/runtime, device tree, fieldbus I/O mapping, search_code/find_references, archive |
| **festo-codesys-mcp** | efranceschetti (E3 Engenharia) | 18 + 12 ide_* + 8 hardware | **Не про «голову», а про дисциплину**: knowledge base (27 тем + 19 мануалов, BM25), 38-block ST-библиотека, генерация PLCopen XML с 3-ступенчатой валидацией (эвристики → XSD TC6 → семантический diff), ~690 тестов. Бесплатно, MIT, Node ≥20 |
| **SuperCodesys** | engenharia-dev | — | Генерация ST + PLCopen XML под Festo CPX-E / Wintec WebVisu; проще festo-codesys-mcp |
| **vulcan-file-ops** | n0zer0d4y | — | ⚠️ НЕ про CODESYS: файловый MCP; в брифе ошибочно сгруппирован |
| **CODESYS Development System MCP Server** | CODESYS GmbH | — | **Официальный**, входит в PDE (арт. 2101000023) — вендорная разработка |

**Вывод**: экосистема развивается в двух направлениях — (1) драйверы IDE
(phobicdotno/ab-mcp/наш плагин, соревнование по охвату и стабильности на
SP21+), (2) «инженерная дисциплина» (festo-codesys-mcp: знания + валидация
перед импортом). Нашему плагину стоит перенять (а) symbol-config инструменты
и (b) идею валидационных гейтов из festo-codesys-mcp.

## Рекомендации по применению

* Серийные правки/сборки — только через тёплый демон (регламент `Rules/02`).
* Онлайн-операции против реального ПЛК — инструменты `codesys_online_*`.
* Новые фичи плагина искать в zbest1000 (источник идей и кода).

## TODO

* [ ] Дозаписать: phobicdotno/NPavii/festo-codesys-mcp/vulcan-mcp/SuperCodesys
      (из брифа) — веб-исследование.
* [ ] Setup-гайды (`03_AI_Prompts_and_MCP/mcp_setup_guides/`) — по локальным
      копиям + README репозиториев.
* [ ] Банк промптов (`03_AI_Prompts_and_MCP/prompts/`) — генерация FB,
      автомат состояний, отладка, оптимизация.
