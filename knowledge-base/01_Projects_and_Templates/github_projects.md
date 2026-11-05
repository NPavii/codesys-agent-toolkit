# GitHub: изученные проекты CODESYS

Дата среза: 2026-09-21. Репозитории изучены локально (клонированы в приватную
папку эталонных материалов; в этот репозиторий не включены — только выводы).

## PackML-бандл (11 репозиториев)

Стандарт ISA TR88.00.02 — фундамент наших программ. Сжатая рабочая выжимка:
[knowledge-base/05_Best_Practices/state_machine_patterns.md](../05_Best_Practices/state_machine_patterns.md).

| Репозиторий | Платформа | Ценность для нас |
|---|---|---|
| LKinGitHub/PackML_CodeSys | CODESYS | Проект-пример + ISA-TR88.00.02-2022 PDF + OMAC guide v2.03 + OPC UA guide |
| Beckhoff-USA-Community/SPT-Libraries | TwinCAT (V3.9/V4) | **Лучшая методология**: MM→EM→Components, Initialize/CyclicLogic, документация docs/ |
| Beckhoff-USA-Community/PackML_PLC_Example | TwinCAT | Целый демо-проект VFFS (PLC) + VFFS_Demo.pdf |
| Beckhoff-USA-Community/PackML_HMI_Example | TcHMI | HMI-часть PackML |
| chris-k84/PackML_Library | TwinCAT | API-обёртка PMLStateMachine (Cycle, PmlStateCommand, RegisterSubUnit) |
| HarriMeskanen/PLC_PackagingMachine | TwinCAT | UnitBaseClass — как PackML-модуль оборачивает машину/робота |
| aljoshakoecher/PackML-StateMachine | Java | Эталон матрицы переходов (невалидные переходы невозможны) |
| peacefighter1996/Open.PackML | C# | Модель PackTags, guard-переходы, tag-tree для OPC UA |
| hijaaack/JB.TcHmiPackMLStateDiagram | TcHMI | Виджет диаграммы состояний |
| point85/OEE-Domain, point85/OEE-Operations | Java | OEE-движок поверх PackML-данных (ISO 22400) |

## Паттерны проектирования (Aliazzzz/Applied-Design-Patterns-in-CODESYS-V3)

7 паттернов ООП в CODESYS V3, каждый — открываемый `.project` + README.
Разбор и канонические реализации: [../05_Best_Practices/oop_patterns.md](../05_Best_Practices/oop_patterns.md).

| Паттерн | Источник | Проекты |
|---|---|---|
| Observer | A. R. Narvaez Contreras | Observer_Application, Observer_Application2 |
| Singleton | A. R. Narvaez Contreras | Singleton_Application, Singleton_Application2 |
| Builder | A. R. Narvaez Contreras | Builder_Application RPi (×2) |
| Decorator | A. R. Narvaez Contreras | Decorator_Application(2) |
| Proxy | A. R. Narvaez Contreras | Proxy_Application |
| Abstract Factory | S. Henneken (блог-экранизация) | Abstract Factory1/2/3 |
| Command | S. Henneken | Command1/2/3 |
| Паттерны LD-логики | — | Patterns of Ladderlogic programming |

Примечание автора репозитория: «паттерны облегчают жизнь, но лучшее решение —
простейшее решение, даже процедурное». Согласуется с `docs/07-standards.md`.

## Прочее

| Репозиторий | Вердикт |
|---|---|
| FieldFox/Codesys-Mqtt-lib | ❌ Не пригодна: каркас MQTT-клиента для **CODESYS V2/WAGO**, тела функций пустые. Детали: [../02_Libraries/mqtt_library.md](../02_Libraries/mqtt_library.md) |

## Веб-обход GitHub 2026-09-21 (краткая карта)

Полный курируемый список ресурсов ST: `myutzy/awesome-structured-text`.

| Репозиторий | Зачем смотреть |
|---|---|
| CiA402 motion layer (pure ST) | Оси без SoftMotion: homing, профильные режимы, CSP; продакшн-истории |
| `damischa1/iec-st-tools` | Конвертация `.st` ↔ CODESYS export ↔ PLCopen XML для CI |
| `Autonomy-Logic/STruCpp` | Компилятор ST → C++17: юнит-тесты ST без ПЛК |
| PLC-виртуальные-комиссии (packaging cell, vision cell) | Примеры PackML + цифровой двойник + OPC UA |
| Open-source ST-форматтер (C#) | CLI/GUI форматирование `.TcPOU` |
| `babos1908/ab-mcp-toolkit` | 75 инструментов MCP над CODESYS (см. БЛОК 3) |

## TODO (БЛОК 1, продолжение)

* [ ] Поиск GitHub: `codesys`, `structured-text`, `IEC61131-3`, `plcopen`,
      `codesys-library`, `codesys-project-template` — с звёздами и датами.
* [ ] Шаблоны проектов: структура POUs, визуализация, CI/CD.
* [ ] Примеры: motion control, диагностика, обработка ошибок.
