# Бесплатные инструменты и плагины

## Форматтеры ST

| Инструмент | Платформа | Примечание |
|---|---|---|
| **STweep Formatter for CODESYS** | Store, арт. 2101000014 | Единый code style; **демо 30 дней** |
| Open-source ST-форматтер (C#) | GitHub | CLI + GUI, выравнивание по таб-колонкам, `.TcPOU`; вдохновлён STWEEP и TcBlack |
| TcBlack | TwinCAT | Форматтер под TwinCAT |
| STweep для TwinCAT | — | Версия под VS/TwinCAT |

## Редакторы и разметка

| Инструмент | Назначение |
|---|---|
| `vscode-st` | Поддержка ST в Visual Studio Code (подсветка, сниппеты) |
| `tree-sitter-structured-text` | Грамматика ST для tree-sitter → редакторы/парсеры |
| Notepad++ ST-синтаксис | Тема подсветки IEC 61131-3 ST |
| `iec-st-tools` (Go) | `.st` ↔ CODESYS 2.3/3.5 export ↔ PLCopen XML (см. БЛОК 2) |

## Линтеры и статический анализ (бесплатные)

| Инструмент | Что делает |
|---|---|
| plc-linter (plc-linter.com) | Статанализ CODESYS/PLCopenXML; 80 проверок: diff-based, целостность FB-инстансов, PLCopen, MISRA-C, IEC 61508/62443 mapping; режим `--metrics` (сложность, вложенность, мёртвый код); GitHub Action / GitLab CI / CLI |
| `iec-checker` | Статанализ IEC 61131-3 (open source) |

## Аддоны CODESYS Store (бесплатные)

| Аддон | Артикул | Назначение |
|---|---|---|
| **CODESYS Security Agent** | 000093 | Управление сертификатами и security-настройками среды; развивается поэтапно |
| Object Oriented Alarming Library (Demo) | 2101000016 | FB создают и активируют свои аварии в Alarm Manager (без ручных списков) — идея близка к SPT Event Logger |
| AnyViz Cloud Adapter | 000089 | PLC как IoT-шлюз, мониторинг/аналитика |
| Iono Pi Library | 000102 | Raspberry Pi I/O-модуль |

## Пакетные менеджеры и CI (TwinCAT-ориентированные, идеи переносимы)

| Инструмент | Назначение |
|---|---|
| Twinpack | Менеджер пакетов библиотек TwinCAT + VS-интеграция |
| zkbuild-action | GitHub Action: сборка + юнит-тесты TwinCAT-проектов |
| CForge / co♻e CI-скрипты | Пайплайн тестов CODESYS через `--runscript` (тикет #64 coUnit) |

## Рекомендации для воркспейса

1. Форматирование: STweep (демо) или open-source форматтер как
   пост-процессинг в пайплайне агента.
2. Качество кода Kimi_Lib: критерий «0 ошибок / 0 предупреждений»
   (`check_all_pool_objects`) + по мере необходимости plc-linter в CI.
3. Новые идеи брать из PDE-инструментов (см.
   [professional_developer_edition.md](professional_developer_edition.md)).
