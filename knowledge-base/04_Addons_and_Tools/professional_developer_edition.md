# CODESYS Professional Developer Edition (PDE)

> Источник: CODESYS Store (store.codesys.com, срез 2026-09-21). Цены — Store
> International; в NA-регионе ориентировочно $550/год (подтверждено тредом
> r/PLC). Демо-лицензия всех инструментов — 30 дней, бесплатно.

## Состав бандла (подписка €550/год, 1 пользователь; floating 5 users от €2750)

| Инструмент | Артикул | Назначение | Версия в бандле (≥2025-02-11) |
|---|---|---|---|
| CODESYS Git | 2101000015 | Нативный Git-клиент в IDE для всех объектов приложения | ≥ 1.3.0.0 |
| CODESYS SVN | 2101000000 | Apache Subversion для исходников | ≥ 4.5.0.0 |
| CODESYS Static Analysis | 2101000002 | Проверка по правилам, метрики качества, code smells, дубли | ≥ 4.3.3.0 |
| CODESYS Profiler | 2101000004 | Замеры времени исполнения и code coverage по блокам | ≥ 2.2.0.0 |
| CODESYS Test Manager | 2101000003 | Автоматизированные тесты приложений/библиотек (system/integration/unit) | ≥ 5.1.0.0 |
| CODESYS UML | 2101000001 | Диаграммы классов и состояний UML | ≥ 4.3.0.0 |
| CODESYS Simulation Interface | — | Связь с симуляторами машин (virtual commissioning) | ≥ 0.9.0.0 |
| CODESYS File-Based Storage | 2101000019 | Текстовое файловое хранение проекта вместо бинарного | ≥ 0.9.0.0 |
| **CODESYS Development System MCP Server** | 2101000023 | **Официальный MCP-сервер CODESYS — подключение LLM к IDE** | входит в PDE |

Лицензирование: CODESYS License Provider ≥1.1.0.0 (ставится автоматически),
активация на soft-container или USB CODESYS Key; workstation-лицензия
переносима переподключением ключа. После истечения подписки проекты
остаются полностью доступны — отключаются только инструменты PDE.

## Выводы для нас

1. **Официальный MCP Server теперь часть PDE** — вендор признал направление;
   наш плагин (см. [mcp_servers_comparison](../03_AI_Prompts_and_MCP/mcp_servers_comparison.md))
   остаётся бесплатной альтернативой с тёплым демоном.
2. File-Based Storage — потенциально интересен для git-diff'ов проектов,
   но для нашего пайплайна (мост + MCP) бинарный `.project` уже решается
   `dump_tree`/native export.
3. Static Analysis и Test Manager — эталонные ориентиры качества; бесплатные
   замены: plc-linter (80 проверок, CI), coUnit (юнит-тесты).

## Бесплатные инструменты (см. free_tools.md)

STweep Formatter (демо 30 дней), CODESYS Security Agent (бесплатный аддон),
CODESYS Depictor (3D, демо 10 поз), vscode-st, tree-sitter-structured-text,
open-source ST-форматтеры (C#, CLI+GUI, `.TcPOU`), CODESYS Doc Export.
