# Правило 03. Работа с проектом CODESYS

Доступ к проектам — только через MCP-инструменты `codesys-mcp` и мост;
прямого доступа к файлам проекта нет. Инструменты работают и с `.project`,
и с `.library` (путь к `.library` — напрямую, без конвертации). У
`.library` нет устройства/задач — компиляцию делать через мост.

## ОКРУЖЕНИЕ

Типовой воркспейс агента (структура, а не конкретный путь):

* `Project/` — рабочие проекты CODESYS (`{{Project_One/Project_one.project}}` и др.).
* `Library/CoDeSyS_Lib/Kimi_Lib.library` — самописная библиотека, **источник истины** (см. «БИБЛИОТЕКА»).
* **Тесты выполняются только на двух файлах:** `Kimi_Lib.library` (контрольная библиотека) и `Project/Project_One/Project_one.project` (тестовый проект). Проверочное зеркало `CoDeSyS_Lib.project` упразднено (2026-09-20): `validate_library` компилирует `.library` напрямую через `check_all_pool_objects()`, без синка в сторонний проект.
* `Library/README.md` — документация по библиотеке; `Library/_ref/` — эталонные материалы (спека PackML, исходники OMAC).

Доступ к проектам — только через MCP-инструменты сервера `codesys-mcp`
(прямого доступа к файлам проекта нет). Все инструменты работают и с `.project`, и с
`.library`: в аргументе пути к проекту указывай полный путь к файлу (`.library` — напрямую,
без конвертации). У `.library` нет устройства/задач — компиляцию делай через мост
(`validate_library`), а не через `codesys_save_project`+build.

* `codesys_project_open`, `codesys_project_info` — открыть/осмотреть проект;
* `codesys_list_objects` — дерево объектов (устройство → Plc Logic → Application → POU);
* `codesys_get_object` — читать declaration/implementation любого объекта (всегда читай существующий код перед изменением!);
* `codesys_create_pou`, `codesys_create_member` (action/method/property), `codesys_create_dut`, `codesys_create_gvl` — создавать объекты;
* `codesys_set_code` — заменить текст declaration/implementation;
* `codesys_save_project` — сохранить.

Каждый вызов инструмента занимает 10–30 с (headless-экземпляр CODESYS). Не делай лишних
вызовов, но никогда не действуй вслепую: сначала `list_objects` + `get_object`, потом изменения.

Новую программу создавай внутри `{{<Устройство>/Plc Logic/Application}}` и обязательно
подключай к задаче (Task Configuration) — без этого она не выполнится.

## ЖЁСТКИЕ ПРАВИЛА РАБОТЫ С ПРОЕКТОМ

1. **Проект не должен быть открыт в GUI CODESYS** — перед началом проверь
   (`tasklist | grep -i codesys`) или предупреди пользователя, иначе конфликт блокировки файла.
2. Все изменения — только через MCP/мост; каждая MCP-операция сохраняет проект автоматически.
3. По завершении — обязательная компиляция и **0 ошибок, 0 предупреждений**; свои ошибки исправляй сам.
4. Не перезаписывай и не удаляй существующие объекты без явной команды пользователя.
5. Если контекста не хватает для однозначной реализации — **приостановись и задай вопросы**, не выдумывай требования.

## Документация на код — MD-файлы, подключённые к проекту

Каждый законченный блок/задача документируется MD-файлом, который
**подключается к проекту** (виден в дереве CODESYS, открывается по F1):
`add_file` моста (режим `link` — файл живёт в `Docs/` рядом с проектом и
правится как обычный текст). Документация на русском, комментарии в коде —
на английском.

## ALARM / NVL / UNIT CONVERSION / ALARMGROUPTEMPLATE (проверено на TestDvo)

Типовая структура Application: `Alarm Configuration` (GUID типа
`c0a56ce5-14a3-4757-ac56-3eab44c974b3`) с детьми — классы Error/Warning/Info
(`b8b46f61-...`), `AlarmStorage`, `AlarmGroup` (`2bef0454-...`); рядом в корне Application:
`AlarmGroupTemplate` (`b85910c7-...`), `NVL` (`ffbfa93a-...`), `UnitConversion`
(`9031c721-...`), `DatasourcesManager`. Задачи `AlarmManagerTask` и `DatasourcesTask` уже
существуют — **новые не создавать**.

* **NVL** — обычный текстовый объект (тип совпадает с GVL: `ffbfa93a-...`). Чтение/наполнение —
  как у GVL: `get_object` читает `textual_declaration`, переменные добавлять/править через
  `set_code` (part=`declaration`) с сохранением существующего текста. Создание новой таблицы —
  `create_gvl` (получится объект того же типа; сетевые настройки донастраиваются в GUI).
  После правки NVL — перечитать `get_object` и убедиться, что старые переменные на месте.
* **Alarm Configuration, AlarmGroup, AlarmGroupTemplate, UnitConversion** — НЕ текстовые
  (нет textual_declaration). Через MCP `set_code` не правятся. Доступ — только через мост:
  объект поддерживает `export_native(path)`, `import_native(path)`, `create_folder(name)`,
  `rename`, `remove`, `move`, `export_xml/import_xml` (eval-шагами, см. «Мост»).
* **`export_xml` для этих объектов НЕ работает** — возвращает пустой PLCopenXML. Для
  чтения/бэкапа используйте **только `export_native`** — это читаемый XML (IArchivable,
  секции EntryList/MetaObject/Object). `create_folder` внутри Alarm Configuration создаёт
  **новый AlarmGroup** (объект типа `2bef0454-...`), а не просто папку — это способ
  создания группы.
* **`import_native` ДОБАВЛЯЕТ объект-копию, а не заменяет существующий** (round-trip экспорт→импорт
  дал `AlarmGroup_1`). Для редактирования: `export_native` → правка XML → удалить старый объект
  → `import_native`. Вложенные GUID-структуры (MetaObject.Guid, ParentGuid, LanguageModelData,
  TextListReference) не переименовывать и не менять — править только содержимое (списки alarms,
  ConversionList, имена переменных). После любого native-импорта — `tree` для контроля
  дубликатов и `build`.
* **AlarmGroupTemplate**: сами алармы лежат внутри объекта (Dictionary `Alarms` в native-XML,
  не дочерними узлами). Дочерних объектов у AlarmGroup/AlarmGroupTemplate нет.
* **UnitConversion**: `ConversionList` в native-XML пустой, если конверсий нет; схему Entry
  брать с реального заполненного объекта (`export_native` → изучить → править по образцу).
* Тестовые/пробные объекты создавать с префиксом `ZZT_` и удалять сразу после проверки.
  Проект TestDvo может правиться параллельными сессиями — чужие изменения в build-ошибках
  (например `_Initialized`/`_Active`) не считать своими; свои пробы откатывать обязательно.
