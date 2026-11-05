# CODESYS Agent Toolkit

Накопленный опыт работы AI-агента (Kimi Work / MCP) с **CODESYS V3** и **CODESYS 4**:
рабочие правила, проверенные на практике грабли, headless-инструменты, база знаний
и датасет решений. Всё свободно используется (MIT) — человеком или агентом.

> CODESYS® — товарный знак 3S-Smart Software Solutions GmbH. Этот репозиторий —
> независимый community-проект и не аффилирован с 3S. Всё содержимое проверено
> на конкретных версиях (CODESYS V3.5 SP21 Patch 1, CODESYS 4 от 2026-10) —
> на других версиях поведение может отличаться.

## Принцип: своя область настраивается пользователем

Репозиторий не навязывает структуру директорий. Вы сами задаёте область
работы: пути к проектам, библиотеке решений и датасету — через конфигурацию
агента, переменные окружения или аргументы. Материалы здесь — правила,
инструменты и образцы, а не готовый воркспейс. Правила агента (`docs/01`)
прямо закрепляют этот принцип.

## Что внутри

```
docs/            Рабочие правила агента (10 глав):
                 01 workflow · 02 bridge/тёплый демон · 03 работа с проектом ·
                 04 своя библиотека решений · 05 внешние библиотеки ·
                 06 ГРАБЛИ (проверено на практике) · 07 стандарты кода ·
                 08 MachineLib (эталонный список элементов) · 09 карта знаний ·
                 10 CODESYS 4 (headless + сессии)
codesys4/        Инструменты для CODESYS 4 без GUI:
                 c4_build.py (headless-сборка через c4-cli bootapp compile),
                 c4_api.py (JSON-RPC/WebSocket + HTTP-файлы), c4_client.py,
                 c4proxy.py (перехват трафика), get_c4_session.py (cookie из
                 WebView2), каталог RPC-методов и эталонный прогон
knowledge-base/  База знаний по экосистеме CODESYS: проекты GitHub, библиотеки,
                 сравнение MCP-серверов, аддоны, ООП/FSM-паттерны, IEC 62443,
                 платформы производителей, официальные ресурсы
dataset/         «Тетрадка проверенных решений»: catalog + записи с вердиктами
                 компиляции (0 ошибок), способом проверки и тегами. Имена
                 рабочих проектов анонимизированы (proj-a / proj-b)
tools/           export_project.py — выгрузка всего кода проекта через тёплый
                 демон (адаптивный обход дерева; каталог моста — env
                 CODESYS_BRIDGE_DIR)
library/         Дизайн-документ референсной библиотеки решений (PackML-фундамент,
                 светофоры, кнопки, пневмоцилиндры, датчики, статистика) —
                 спецификации блоков и история версий. Файлы CODESYS-приложений
                 (`.project`/`.library`) в репозиторий не включены
```

## Быстрый старт

**Мне нужно автоматизировать CODESYS V3** — ставьте
[codesys-mcp-server](https://github.com/NPavii/codesys-mcp-server) (MCP-сервер с
46+ операциями над проектом) и читайте `docs/02-bridge.md` (тёплый демон:
ускорение ~20×) и `docs/06-pitfalls.md` (обязателен до незнакомых операций).

**Мне нужна headless-сборка CODESYS 4**:

```bash
set C4_CLI=C:\path\to\c4-cli.exe
python codesys4/c4_build.py C:\path\to\project.fbsdev
```

**Я настраиваю агента** — отдайте ему `docs/` как системные правила
(это и есть «навыки»: workflow, порядок поиска решений, чек-листы, грабли),
затем укажите пути к своей области.

## Связанные проекты

- [NPavii/codesys-mcp-server](https://github.com/NPavii/codesys-mcp-server) —
  MCP-сервер для CODESYS V3 (ScriptEngine, мост, тёплый демон), на который
  ссылаются правила из `docs/02`.

## Примечания

- Документы `docs/` — рабочие правила автора: локальные пути приведены как
  ориентир; в своей области используйте свои.
- Файлы CODESYS-приложений (`.project`, `.library`, `.compiled-library`) в
  репозиторий не включены намеренно — распространять чужие/рабочие проекты
  нельзя; дизайн библиотеки воспроизводится по `library/README.md`.
- Скрипты `codesys4/` работают с недокументированным интерфейсом CODESYS 4:
  могут сломаться в любой новой версии. Проверено на сборке от 2026-10-30.

## English summary

A practitioner's knowledge base for AI agents (and humans) working with CODESYS
V3/V4: agent operating rules, an empirically verified pitfalls catalog, headless
build tooling for CODESYS 4 (`c4-cli bootapp compile`, JSON-RPC/WebSocket API),
a curated knowledge base and a dataset of compiler-verified solutions. Users
configure their own workspace area — the repo ships rules and tools, not
projects. CODESYS application files (`.project`/`.library`) are intentionally
excluded. MIT licensed.

## Лицензия

[MIT](LICENSE) © 2026 Pavel (NPavii).
