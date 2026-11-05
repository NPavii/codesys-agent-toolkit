# Документация и мануалы: ключевые ссылки

## Официальные ресурсы CODESYS

| Ресурс | URL | Что там |
|---|---|---|
| Online Help | `content.helpme-codesys.com` | Полная документация по IDE, библиотекам, рантайму; есть оглавление Security (`/Security/_sec_start_page.html`) |
| CODESYS Store | `store.codesys.com` | Аддоны, библиотеки, рантаймы; бесплатные демо почти всего |
| CODESYS Forge | `forge.codesys.com` | Официальное community: проекты (coUnit), форум, тикеты |
| CODESYS Wiki (CN) | `wiki.codesys.cn` | Китайская база знаний |
| Security Whitepaper | codesys.com (раздел Security) | Меры безопасности CODESYS, процесс по IEC 62443 |
| CODESYS Academy | codesys.com/academy | Платные курсы (напр. Application Composer €1254) |

## Сторонние базы знаний и списки

| Ресурс | Что там |
|---|---|
| `myutzy/awesome-structured-text` (GitHub) | Курируемый список: IDE, тестинг (coUnit/TcUnit/UniTest), компиляторы (matiec, RuSTy, blark, iec-checker), библиотеки (OSCAT, structured-text-utilities, TcOpen), расширения (STweep, vscode-st, tree-sitter), DevOps (Twinpack, zkbuild-action), книги, курсы, каналы |
| Stefan Henneken IEC 61131-3 Blog | ООП и паттерны в IEC 61131-3 (источник паттернов из `Library/_ref/Applied-Design-Patterns-in-CODESYS-V3/`) |
| PLCopen | `plcopen.org` — стандарты (Motion, TC6 XML, OPC UA mapping) |
| OMAC | `omac.org` — PackML Implementation Guide (бесплатно) |
| ISA | `isa.org` — TR88.00.02-2022 (платно; копия есть в `Library/_ref/PackML/PackML_CodeSys/doc/`) |

## Курсы и видео (из awesome-списка и веб-обхода)

| Ресурс | Формат |
|---|---|
| Jakob Sagatowski — PLC programming using TwinCAT 3 | 18-эпизодный бесплатный курс (YouTube) |
| Gary Pratt — OOIP using CODESYS | CODESYS Tech Talk (OOP) |
| ControlByte Academy | Платные курсы ST с упражнениями |
| RealPars | Курсы PLC (многоуровневые) |
| r/PLC, PLCtalk, Control.com | Форумы/сообщества |

## FAQ и грабли (сводно)

| Симптом | Причина | Решение |
|---|---|---|
| `C:\Program is not recognized` в MCP | npx + пробелы в путях | Запускать `codesys-mcp-tool` напрямую |
| Library Manager показывает пакет, POUs не видны | namespace не добавлен в дерево | Drag namespace в application |
| «Library not present on device» | запрещена выгрузка библиотек | Online → Library Management → implicit download |
| Конфликт имён после OSCAT | совпадения со Standard | qualified_only / префиксы |
| `.lib` (V2) не открывается | формат V2 | брать V3 `.library` |
| TwinCAT не принимает CODESYS-библиотеку | битая ссылка/разные системные библиотеки | править ссылки; лучше использовать порт под TwinCAT |

Постоянная пополняемая карта граблей этой машины — `Rules/06-pitfalls.md`
(источник истины, сюда не дублировать).
