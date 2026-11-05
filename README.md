# CODESYS Agent Toolkit

Накопленный опыт работы AI-агента (Kimi Work / MCP) с **CODESYS V3** и **CODESYS 4**:
рабочие правила, проверенные на практике грабли, headless-инструменты, база знаний,
датасет решений и библиотека готовых функциональных блоков. Всё свободно
используется (MIT) — человеком или агентом.

> CODESYS® — товарный знак 3S-Smart Software Solutions GmbH. Этот репозиторий —
> независимый community-проект и не аффилирован с 3S. Всё содержимое проверено
> на конкретных версиях (CODESYS V3.5 SP21 Patch 1, CODESYS 4 от 2026-10) —
> на других версиях поведение может отличаться.

## Что внутри

```
docs/            Рабочие правила агента (10 глав):
                 01 workflow · 02 bridge/тёплый демон · 03 работа с проектом ·
                 04 Kimi_Lib · 05 внешние библиотеки · 06 ГРАБЛИ (238 строк,
                 проверено на этой машине) · 07 стандарты кода · 08 MachineLib ·
                 09 карта знаний · 10 CODESYS 4 (headless + сессии)
codesys4/        Инструменты для CODESYS 4 без GUI:
                 c4_build.py (headless-сборка через c4-cli bootapp compile),
                 c4_api.py (JSON-RPC/WebSocket + HTTP-файлы), c4_client.py,
                 c4proxy.py (перехват трафика), get_c4_session.py (cookie из
                 WebView2), каталог RPC-методов и эталонный прогон
knowledge-base/  База знаний по экосистеме CODESYS: проекты GitHub, библиотеки,
                 сравнение MCP-серверов, аддоны, ООП/FSM-паттерны, IEC 62443,
                 платформы производителей, официальные ресурсы
dataset/         «Тетрадка проверенных решений»: catalog + записи с вердиктами
                 компиляции (0 ошибок), способом проверки и тегами
tools/           export_project.py — выгрузка всего кода проекта через тёплый
                 демон (адаптивный обход дерева, ~7 с на 119 объектов)
library/         Kimi_Lib.library — библиотека готовых решений (PackML-фундамент,
                 светофоры, кнопки, пневмоцилиндры, датчики, статистика).
                 Компилируется с 0 ошибок / 0 предупреждений. Состав — в library/README.md
```

## Быстрый старт

**Мне нужно автоматизировать CODESYS V3** — ставьте
[codesys-mcp-server](https://github.com/NPavii/codesys-mcp-server) (MCP-сервер с
46+ операциями над проектом) и читайте `docs/02-bridge.md` (тёплый демон:
ускорение ~20×) и `docs/06-pitfalls.md` (обязателен до незнакомых операций).

**Мне нужна headless-сборка CODESYS 4**:

```bash
set C4_CLI=C:\Program Files\CODESYS 4\CODESYS-4.exe   # или путь к c4-cli.exe
python codesys4/c4_build.py C:\path\to\project.fbsdev
```

**Мне нужны готовые FB** — `library/Kimi_Lib.library` + `library/README.md`
(как подключить: копированием или «Save as compiled library»).

**Я настраиваю агента** — отдайте ему `docs/` как системные правила
(это и есть «навыки»: workflow, порядок поиска решений, чек-листы, грабли).

## Связанные проекты

- [NPavii/codesys-mcp-server](https://github.com/NPavii/codesys-mcp-server) —
  MCP-сервер для CODESYS V3 (ScriptEngine, мост, тёплый демон), на который
  ссылаются правила из `docs/02`.
- Код библиотеки зависит от vendor-библиотеки 3S `OMAC_PackML_State_Machine`
  (namespace `PACK_ML`) и системной `Standard` (TON/R_TRIG) — обе поставляются
  с CODESYS.

## Примечания

- Документы `docs/` — рабочие правила автора: пути вроде `Library/_ref/`,
  `Project/...`, `CodeSYS-MCP/bridge/` относятся к исходному воркспейсу и
  приведены как ориентир, а не как обязательная структура.
- Скрипты `codesys4/` работают с недокументированным интерфейсом CODESYS 4:
  могут сломаться в любой новой версии. Проверено на сборке от 2026-10-30.

## English summary

A practitioner's knowledge base for AI agents (and humans) working with CODESYS
V3/V4: agent operating rules, an empirically verified pitfalls catalog, headless
build tooling for CODESYS 4 (`c4-cli bootapp compile`, JSON-RPC/WebSocket API),
a curated knowledge base, a dataset of compiler-verified solutions, and Kimi_Lib —
a ready-to-use IEC 61131-3 library built on PackML. MIT licensed.

## Лицензия

[MIT](LICENSE) © 2026 Pavel (NPavii). Код библиотеки Kimi_Lib — тоже MIT.
