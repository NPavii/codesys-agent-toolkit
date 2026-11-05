# Правило 07. Стандарты кода и структура эталонного проекта (Rulebook)

Свод правил эталонного проекта CODESYS: структура, задачи, типы POU и ООП,
поведенческий шаблон PLCopen, именование, хранение переменных, Alarm
Manager, качество, чек-листы. (§8 «Библиотеки» перенесён в docs/05,
§12 «Шаблон ТЗ» — в docs/01, §13 «Источники» — в конце этого файла.)

# ГЛАВА 3. CODESYS Rulebook — свод правил эталонного проекта

---

## 0. Главный принцип (TL;DR)

**Эталонный проект CODESYS — это не «программа», а продукт:** состояния машины вместо флагов, объекты вместо разрозненных переменных, библиотеки вместо копипасты, конфигурация аварий вместо разбросанных IF-ов, Git вместо «проект_финал_v7_final.project».

Этот свод правил отвечает на вопрос: «что должен сделать агент, чтобы проект использовал всю мощь CODESYS, а не повторял практики 2005 года». Каждое правило помечено приоритетом: **[HIGH]** — нарушение ломает проект; **[MED]** — нарушение усложняет поддержку; **[LOW]** — вопрос единообразия.

> **Примечание.** **Связь с MachineLib:** библиотека состояний машины (PackML, светофор, кнопки, аварии) из соседнего документа — это эталонная реализация разделов 3, 4 и 7 этого свода. Правила здесь — «почему так», MachineLib — «как именно».

---

## 1. Структура эталонного проекта

Дерево проекта должно быть предсказуемым: агент, открывший любой проект компании, обязан сориентироваться за минуту. Эталонная структура:

```iecst
Project
├── POUs (project-wide, видны всем приложениям)
│   ├── DUT/                      // структуры, enum, union — ВСЕ пользовательские типы
│   ├── LIB_Core/                 // собственные базовые FB (MachineLib и т.п.)
│   ├── LIB_Devices/              // FB устройств: клапан, мотор, ПЦ, датчик
│   └── PRG_Template              // шаблоны программ
└── Devices
    └── PLC (Device)
        └── Application
            ├── Task Configuration   // см. раздел 2
            ├── GVL_IO               // единственная точка привязки физических I/O
            ├── GVL_HMI              // обмен с визуализацией
            ├── GVL_Param            // настройки станка (подмножество — retain)
            ├── NVL_ToLine (sender)  // обмен с другими контроллерами
            ├── PersistentVars       // единственный список persistent
            ├── Alarm Configuration  // см. раздел 7
            ├── Symbol Configuration // OPC UA наружу — только через него
            ├── Visualization        // HMI
            ├── PRG_Main             // оркестрация: вызывает подпрограммы
            ├── PRG_Safety           // программная диагностика безопасных цепей
            ├── PRG_Station01..N     // программы по станциям/узлам
            └── PRG_Diagnostics      // сбор аварий, статистика, журнал
```

**[HIGH]** **Правило S1-1. Один объект — одна ответственность, разбивка по узлам машины, а не по типам сигналов.** Группируйте по физическим узлам («узел запайки», «конвейер подачи»), а не «все клапаны в одной программе, все датчики в другой». Сообщество CODESYS прямо рекомендует реляционную модель группировки вместо функциональной: объект = узел/девайс, а не «раздел с клапанами» (CODESYS Forge, «Advice on OOP Code Structure»: 2016-08-28([https://forge.codesys.com/forge/talk/Engineering/thread/49f235f440/](https://forge.codesys.com/forge/talk/Engineering/thread/49f235f440/))).

**[HIGH]** **Правило S1-2. Физические адреса существуют ровно в одном месте — GVL_IO.** PLCopen Rule N1: использование жёстко зашитых физических адресов в программе запрещено — всегда объявляйте переменную (PLCopen Coding Guidelines v1.0, Rule N1: 2016-04-20([https://www.plcopen.org/download_file/force/ff60e817-eee5-442d-b718-a357a7279c7e/342/](https://www.plcopen.org/download_file/force/ff60e817-eee5-442d-b718-a357a7279c7e/342/))). Весь код работает с символическими именами; перенос на другое железо = правка одной GVL.

**[MED]** **Правило S1-3. GVL в POUs view ≠ GVL в Application.** GVL, добавленная под приложением, видна только внутри приложения; GVL в представлении POUs видна всему проекту (CODESYS Online Help, Object GVL: без даты([https://help.codesys.com/api-content/2/codesys/3.5.13.0/en/_cds_obj_gvl/](https://help.codesys.com/api-content/2/codesys/3.5.13.0/en/_cds_obj_gvl/))). По умолчанию — под приложением: меньше соблазна глобальной грязи.

**[MED]** **Правило S1-4. Всё, что можно положить в библиотеку, — в библиотеку.** Повторно используемый код не живёт в проекте: он живёт в пользовательской библиотеке с версией и namespace (раздел 9).

---

## 2. Конфигурация задач (Task Configuration)

Каждое приложение обязано иметь объект Task Configuration — это «диспетчер» вызовов программ: имя, приоритет, тип (cyclic / freewheeling / event / status), watchdog (CODESYS Help, Task Configuration: без даты([https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_f_task_configuration.html](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_f_task_configuration.html))).

### Эталонный набор задач

| Задача | Тип | Интервал | Приоритет (0 = выше всех) | Назначение |
|---|---|---|---|---|
| MotionTask | Cyclic / EtherCAT sync | 1–4 мс (цикл шины) | 1 | SoftMotion, синхронизация осей |
| FastTask | Cyclic | 5 мс | 5 | Быстрые I/O, блокировки, счётчики |
| MainTask | Cyclic | 10–20 мс | 10 | PRG_Main и вся логика станка |
| VisuTask | Cyclic | 100–200 мс | 31 | Визуализация |

Рекомендуемая иерархия задач для EtherCAT/SoftMotion — Industrial Monitor Direct: 2026-04-04([https://industrialmonitordirect.com/blogs/knowledgebase/codesys-cyclic-vs-freewheeling-task-configuration-best-practices](https://industrialmonitordirect.com/blogs/knowledgebase/codesys-cyclic-vs-freewheeling-task-configuration-best-practices)); для визуализации интервал 200–400 мс и самый низкий приоритет 31 — АИП: 2019-02-20([https://aip.com.ru/article/vizualizatsiya_v_srede_codesys](https://aip.com.ru/article/vizualizatsiya_v_srede_codesys)).

**[HIGH]** **S2-1. MainTask — всегда cyclic, не freewheeling.** Freewheeling-задачи насыщают CPU и вызывают проблемы с подключением при отладке и online change (Industrial Monitor Direct: 2026-04-04, ссылка выше). Freewheeling допустим только для тривиальных приложений без коммуникаций.

**[HIGH]** **S2-2. Уникальные приоритеты.** Каждой задаче — своё значение приоритета (меньше = важнее), иначе порядок исполнения непредсказуем (Weintek forum: 2024-12-10([https://forum.weintekusa.com/t/how-to-optimize-task-management-in-codesys/2560](https://forum.weintekusa.com/t/how-to-optimize-task-management-in-codesys/2560))).

**[HIGH]** **S2-3. Интервал ≥ 2–3× худшего времени исполнения.** Измерьте worst-case время задачи (Last Cycle Time при самом тяжёлом сценарии) и дайте запас ×2–3; включите watchdog на каждой задаче (Weintek forum: 2024-12-10, ссылка выше).

**[MED]** **S2-4. Все задачи делят одну карту образа процесса.** Консистентность данных между задачами разных приоритетов — ваша забота (копируйте данные пакетом, при необходимости SysSem) (CODESYS Help, Task Configuration, ссылка выше).

**[MED]** **S2-5. Никаких блокирующих циклов.** Код в задаче выполняется за скан: WHILE с непредсказуемым выходом, ожидание «пока датчик сработает» внутри цикла — запрещены. Ждать — через состояния и таймеры между сканами.

---

## 3. Выбор типа POU и ООП

CODESYS V3 поддерживает полноценное ООП по IEC 61131-3 3rd edition: `FUNCTION_BLOCK ... EXTENDS / IMPLEMENTS`, `INTERFACE`, `METHOD`, `PROPERTY`, `THIS^`, `SUPER^`, спецификаторы доступа `PUBLIC/PRIVATE/PROTECTED` (Systems Integrated, CODESYS OOP Training PAC108([https://www.systemsintegrated.com/training/SI%20PAC%20V3%20108%20Object%20Oriented%20v1.pdf](https://www.systemsintegrated.com/training/SI%20PAC%20V3%20108%20Object%20Oriented%20v1.pdf))). Этим нужно пользоваться — это и есть «мощь платформы».

### 3.1. Выбор типа POU

| Тип | Когда | Пример |
|---|---|---|
| FUNCTION | Чистое вычисление без состояния; один вход → один результат | масштабирование аналога, CRC |
| FUNCTION_BLOCK | Всё, у чего есть состояние/память: устройства, регуляторы, автоматы | FB_Valve, FB_PackML |
| PROGRAM | Оркестрация верхнего уровня, привязка к задаче; единственный тип, который можно вешать на task | PRG_Station01 |
| METHOD | Операция над объектом (команда, действие) | M_Command(), M_Reset() |
| PROPERTY | Чтение/запись с логикой (вычисляемое значение, валидация) | P_StateText |
| ACTION | Разбиение большого тела FB/PRG по фазам | ACT_Init, ACT_Run |

Базовое правило выбора: FB — состояние, FUN — чистая математика, PRG — оркестрация задачи; компактный интерфейс: VAR_INPUT — команды и измерения, VAR_OUTPUT — статусы, VAR — скрытое состояние (codesys-mcp writing guidance, CODESYS Help: POU / Function Block([https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_obj_function_block.html](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_obj_function_block.html))).

### 3.2. Правила ООП

**[HIGH]** **OOP-1. Инкапсуляция по умолчанию.** Внутреннее состояние — в `VAR` (не VAR_OUTPUT). Наружу: входы, выходы, методы, свойства. PLCopen CP5: приложения должны проектироваться с принципами ООП — модуляризация и инкапсуляция, PRIVATE-данные в FB (PLCopen Coding Guidelines, Rule CP5: 2016-04-20([plcopen.org](https://www.plcopen.org/download_file/force/ff60e817-eee5-442d-b718-a357a7279c7e/342/))).

**[HIGH]** **OOP-2. Никаких VAR_EXTERNAL и прямых обращений к глобалам изнутри FB.** PLCopen CP6: FB/классы не должны использовать внешние переменные — нужные данные передавайте через параметры (PLCopen Coding Guidelines, Rule CP6: 2016-04-20, тот же источник). FB, дёргающий GVL напрямую, непереносим и нетестируем. Нужна связь с железом — передавайте `REFERENCE TO` через FB_INIT или метод привязки (паттерн «MapLink» из сообщества (CODESYS Forge, OOP thread: 2016-08-28([forge.codesys.com](https://forge.codesys.com/forge/talk/Engineering/thread/49f235f440/)))).

**[MED]** **OOP-3. Общее поведение — через INTERFACE.** Все приводы реализуют `I_Drive`, все клапаны — `I_Valve`. FB, реализующий интерфейс, обязан реализовать все его методы и свойства; CODESYS автоматически вставляет требуемые методы под FB, но при добавлении методов в интерфейс позже нужно повторно вызывать «Implement Interface» (CODESYS Help, Implementation of an Interface([helpme-codesys.com](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_implementing_interface.html))).

**[MED]** **OOP-4. EXTENDS — для «является разновидностью», композиция — для «имеет часть».** Наследование не для копирования кода. Базовый FB абстрактен и не содержит прикладной логики станка.

**[MED]** **OOP-5. PROPERTY — не переменная.** Свойство — это get/set-функция: его нельзя напрямую привязать к элементу визуализации или использовать там, где нужна ссылка на память; для отладки добавляйте `{attribute 'monitoring' := 'call'}` (CODESYS Forge, OOP thread: 2016-08-28, ссылка выше). Для HMI дублируйте значение в VAR_OUTPUT.

**[HIGH]** **OOP-6. Арифметика указателей запрещена.** PLCopen E2: указатели — только сравнение с NULL и присваивание; никакой адресной арифметики (PLCopen Coding Guidelines, Rule E2: 2016-04-20, ссылка выше). REFERENCE TO — да, `ADR()`+смещение — нет.

**[MED]** **OOP-7. Мелкие FB лучше крупных.** «Чем мельче разбита вещь, тем лучше определение, реализация и отладка» — опыт внедрений ООП в CODESYS (CODESYS Forge: 2016-08-28, ссылка выше). Один датчик — один FB, а не «FB модуля из 16 входов».

---

## 4. Поведенческий шаблон PLCopen (Execute/Done/Busy/Error)

Все FB с «действием во времени» (запрос, движение, операция) должны выглядеть как PLCopen-блок. Тогда любой, кто видел `MC_MoveAbsolute`, понимает ваш FB без документации.

```iecst
VAR_INPUT
    bExecute : BOOL;   // старт по переднему фронту; параметры читаются один раз на фронте
    // ... параметры операции
END_VAR
VAR_OUTPUT
    bDone           : BOOL;  // успех
    bBusy           : BOOL;  // работа идёт
    bActive         : BOOL;  // FB реально управляет ресурсом
    bCommandAborted : BOOL;  // прерван другой командой
    bError          : BOOL;  // ошибка
    nErrorID        : INT;   // код ошибки
END_VAR
```

**[HIGH]** **PB-1. Статусные выходы взаимоисключаемы.** В каждый момент времени TRUE может быть только один из Done / Busy / CommandAborted / Error (ICP DAS, PLCopen Motion Control User Manual([icpdas.com](https://www.icpdas.com/web/product/download/industrial_communication/ethercat/document/manual/PLCopen_User_Manual_en_v1.1.pdf))).

**[HIGH]** **PB-2. Параметры читаются на фронте Execute.** Изменение входов во время работы не влияет на текущую операцию (кроме блоков с ContinuousUpdate) (simatic-ax/plcopen-snippets: 2023-05-09([github.com/simatic-ax/plcopen-snippets](https://github.com/simatic-ax/plcopen-snippets))).

**[HIGH]** **PB-3. Завершение — минимум один цикл.** Done/Error/CommandAborted удерживаются минимум один скан, даже если Execute уже снят (ICP DAS manual, ссылка выше). При снятии Execute после завершения выходы сбрасываются.

**[MED]** **PB-4. Модель Enable — для уровневых блоков.** Enable-блоки (типа MC_Power) читают входы каждый скан и при снятии Enable обнуляют выходы (Yaskawa, Creating PLCopen Compliant Function Blocks([yaskawa.com](https://www.yaskawa.com/delegate/getAttachment?documentId=AN.MWIEC.01&cmd=documents&documentName=AN.MPIEC.01%20Creating%20PLCopen%20Compliant%20function%20blocks.pdf))). Не смешивайте Execute и Enable в одном FB без необходимости.

**[MED]** **PB-5. Состояние машины — enum, не флаги.** `eState : E_PackMLState` вместо пяти BOOL. См. модуль FB_PackML в MachineLib.

---

## 5. Именование переменных

Единый стандарт именования — это то, что позволяет агенту (и человеку) читать чужой код. База — PLCopen Coding Guidelines v1.0, раздел Naming Rules (PLCopen: 2016-04-20([plcopen.org](https://www.plcopen.org/download_file/force/ff60e817-eee5-442d-b718-a357a7279c7e/342/))).

### 5.1. Префиксы типов (PLCopen)

| Префикс | Тип | Пример |
|---|---|---|
| `x / b` | BOOL | bEnable, bError |
| `si / i / di / li` | SINT / INT / DINT / LINT | iSpeed, diCounter |
| `usi / ui / udi / uli` | USINT / UINT / UDINT / ULINT | uiStatus |
| `r / lr` | REAL / LREAL | rSetpoint, lrEnergy |
| `tim / ltim` | TIME / LTIME | timTimeout |
| `tod / dt` | TIME_OF_DAY / DATE_AND_TIME | dtLastAlarm |
| `s / ws` | STRING / WSTRING | sMessage |
| `by / w / dw / lw` | BYTE / WORD / DWORD / LWORD | dwConfigBits |
| `e` | ENUM | eState, eCmd |
| `st` | STRUCT | stRecipe |
| `a` | ARRAY | aCylinders |
| `fb` | экземпляр FUNCTION_BLOCK | fbPackML, fbTower |
| `p / ref` | POINTER / REFERENCE TO | refSensor |

Таблица префиксов — PLCopen Coding Guidelines v1.0, раздел 3.1: 2016-04-20 (ссылка выше). Префикс экземпляра FB `fb` — сложившаяся практика сообщества.

### 5.2. Префиксы областей и ролей

| Префикс | Значение | Пример |
|---|---|---|
| `ix / iw / id` | Физический вход BOOL / WORD / DWORD | ixStartButton, iwPressure |
| `qx / qw / qd` | Физический выход BOOL / WORD / DWORD | qxValve1 |
| `GVL_` | Имя глобального списка (используется как namespace) | GVL_IO.ixStartButton |
| `E_ / ST_ / FB_ / I_ / PRG_ / F_` | Типы: enum / struct / function block / interface / program / function | E_PackMLState, I_Drive |
| `M_ / P_` | Метод / свойство внутри FB | M_Command, P_StateText |
| `C_` или UPPER_SNAKE_CASE | Константы (VAR CONSTANT) | MAX_CYLINDERS |

Префиксы ix/qx для физических I/O — Prybisch Automation, PLC Best Practices: 2025-09-20([prybisch-automation.eu](https://prybisch-automation.eu/en/blog/plc-programming-best-practices)); префиксы типов объектов (FB, E, ST, I, PRG) — PLCopen, раздел 3.2.8: 2016-04-20 (ссылка выше).

### 5.3. Жёсткие правила имён

**[HIGH]** **N-1. Запрещены имена, совпадающие с ключевыми словами, типами IEC и именами стандартных библиотек.** И запрещены бессмысленные имена: Info, Data, Temp, Buf (PLCopen Rule N3).

**[HIGH]** **N-2. Локальное имя не должно затенять глобальное.** PLCopen Rule N5: никаких локальных `i`, если есть глобальный `i`; счётчики циклов внутри FB — `_i`.

**[MED]** **N-3. Единый регистр:** UpperCamelCase для объектов и переменных, UPPER_SNAKE_CASE для констант (PLCopen Rule N4). Длина имён 8–25 символов, без экзотических сокращений (PLCopen Rule N6).

**[MED]** **N-4. Только ASCII, без цифры в начале, без кириллицы в идентификаторах** (PLCopen Rule N8). Кириллица — в комментариях и текстах аварий.

**[MED]** **N-5. Формальный вызов с именами параметров.** Для пользовательских FB — вызов с `:=` и `=>`, по параметру на строку при длинных списках (PLCopen Rule L14).

**[LOW]** **N-6. Комментарии — однострочные `//`** (PLCopen Rule C5): многострочные `(* *)` опасны при вложенности; их можно использовать лишь для временного отключения кода при отладке.

---

## 6. Где хранить переменные: локальные / GVL / NVL / Retain / Persistent

Матрица принятия решения — главное правило данных проекта:

| Хранилище | Что туда класть | Чего туда НЕ класть |
|---|---|---|
| **VAR (локальные в FB/PRG)** | Всё по умолчанию. Состояние, таймеры, счётчики объекта | Данные, нужные другим POU или HMI |
| **GVL_IO** | Привязка физических I/O (%IX/%QX), единственное место с адресами | Логические переменные без привязки к железу |
| **GVL_HMI** | Обмен с визуализацией: уставки, статусы, команды оператора | Внутренние расчёты |
| **GVL_Param** | Настройки машины, конфигурация станций | — |
| **NVL (Network Variable List)** | Обмен ПЛК↔ПЛК по UDP: компактные структуры состояния + heartbeat | Большие массивы, строки отчётов |
| **VAR RETAIN** | Данные, переживающие сбой питания: счётчики продукции, позиции | Всё подряд (область retain ограничена) |
| **PersistentVars (PERSISTENT)** | Данные, переживающие загрузку новой программы: калибровки, обученные пороги | — (список в проекте только один) |
| **Symbol Configuration** | Экспорт наружу (OPC UA, SCADA) — только помеченные `{attribute 'symbol'}` переменные | Вся GVL «на всякий случай» |

### Правила GVL

**[HIGH]** **G-1. Каждая GVL — с `{attribute 'qualified_only'}`.** Обращение только как `GVL_IO.ixStart`: имя списка становится namespace, конфликты имён исчезают, поиск использования тривиален. Снятие атрибута «для удобства» превращает проект в помойку глобалов (CODESYS Forge, «Using globals without a prefix»: 2018-09-18([forge.codesys.com](https://forge.codesys.com/forge/talk/Engineering/thread/aefe83c65b/))).

**[MED]** **G-2. GVL — не шина данных между FB.** Обмен между объектами — через параметры/VAR_IN_OUT/интерфейсы. GVL только для: I/O, HMI, параметров, межконтроллерного обмена.

### Правила NVL

**[MED]** **NVL-1. Sender экспортирует .gvl, Receiver импортирует именно этот файл** — объявления гарантированно идентичны (CODESYS Help, Configuring a Network Variable Exchange([help.codesys.com](https://help.codesys.com/api-content/2/codesys/3.5.13.0/en/_cds_configuring_network_variables_exchange/))). Опции: Pack variables, Add checksum, Cyclic transmission.

**[MED]** **NVL-2. Всегда включайте heartbeat-счётчик.** Приёмник проверяет, что счётчик меняется; замер — авария связи. Это стандартный паттерн диагностики NVL (WAGO Community: 2023-09-11([wago.community](https://www.wago.community/t/best-solution-for-two-way-communication/590))).

**[LOW]** **NVL-3. Переменная NVL — до 255 байт; при превышении телеграммы данные могут быть неконсистентны** — держите списки компактными (WAGO Community, та же ветка).

### Правила Retain/Persistent

**[HIGH]** **RP-1. Persistent — только в списке PersistentVars.** Список persistent-переменных в приложении один; локальные `VAR PERSISTENT` всё равно компилируются в него — объявляйте сразу там, чтобы видеть весь объём (CODESYS应用指南: 2024([справка по CODESYS](http://23.226.181.16:9032/article/425.html))).

**[MED]** **RP-2. Изменение структуры retain/persistent — это миграция данных.** Перед загрузкой новой версии на работающий станок: зафиксировать текущие значения, проверить поведение после download. Агент обязан предупреждать пользователя об изменении retain-раскладки.

**[MED]** **RP-3. Доступ к retain из FB — через REFERENCE TO с безопасным дефолтом.** Неинициализированная ссылка = исключение; назначайте dummy-переменную по умолчанию (CODESYS Forge, OOP thread: 2016-09-25([forge.codesys.com](https://forge.codesys.com/forge/talk/Engineering/thread/49f235f440/))).

---

## 7. Alarm Manager — аварии как конфигурация, а не код

CODESYS имеет штатную систему аварий: объекты **Alarm Configuration → Alarm Class / Alarm Group / Alarm Storage**, отображение в визуализации элементами Alarm Table и Alarm Banner (PLC BLOG, CODESYS Alarm Management([plcblog.in](https://plcblog.in/plc/codesys/CODESYS%20Alarm%20Management%20and%20configuration.php))). Используйте её вместо самодельных массивов BOOL, если проект имеет HMI на CODESYS Visualization.

### 7.1. Эталонная конфигурация

| Класс | Приоритет (0 = высший) | Квитирование | Архивация | Смысл |
|---|---|---|---|---|
| Error | 0–49 | REP_ACK (устранил + квитировал) | Да | Остановка/авария, требует вмешательства |
| Warning | 50–149 | REP | Да | Отклонение, работа продолжается |
| Info | 150–255 | Нет | По желанию | События: смена режима, вход оператора |

Приоритет класса 0–255 (0 — высший), методы квитирования REP / ACK / REP_ACK / ACK_REP / ACK_REP_ACK, архивация через Alarm Storage — PLC BLOG, CODESYS Alarm Management([plcblog.in](https://plcblog.in/plc/codesys/CODESYS%20Alarm%20Management%20and%20configuration.php)); настройка классов Error/Warning/Info и Alarm Table — Bosch Rexroth ctrlX how-to: 2026-01-13([community.boschrexroth.com](https://community.boschrexroth.com/ctrlx-automation-how-tos-qmglrz33/post/how-to-use-the-alarm-management-from-codesys-V12Q2qWs1v4KWkU)).

### 7.2. Правила

**[HIGH]** **AM-1. Авария = строка в Alarm Group, не IF в коде.** В коде остаётся только триггер-переменная (Observation Type: Digital / Upper Limit / Event). Текст, класс, задержки (On/Off-Delay), latch-переменные — в конфигурации (Bosch Rexroth how-to: 2026-01-13, ссылка выше).

**[MED]** **AM-2. Latch-переменные для контекста.** К аварии прикрепляйте 1–2 latch-переменные (температура, скорость в момент аварии) — это бесценно при разборе инцидентов (Zenn, разбор CODESYS Example Project Alarm Manager: 2025-03-28([zenn.dev](https://zenn.dev/kzchd/articles/06bb7ff4b35e62))).

**[MED]** **AM-3. Сообщение = проблема + место + действие.** «Датчик Х3: залипание — очистите датчик» вместо «Ошибка 14». Сообщение должен понимать оператор, а не программист (Bosch Rexroth how-to: 2026-01-13, ссылка выше).

**[MED]** **AM-4. Archiving включать осознанно.** Alarm Storage пишет в SQLite на контроллере; экспорт — CSV через контекстное меню AlarmStorage (CODESYS应用指南: 2024([справка по CODESYS](http://23.226.181.16:9032/article/425.html))). Для класса Info архивацию обычно выключают.

**[MED]** **AM-5. Программный модуль аварий (MachineLib FB_AlarmManager) и CODESYS Alarm Manager — не дублируют, а питают друг друга.** FB модуля формируют триггер-биты; Alarm Group наблюдает эти биты и даёт тексты/архив/HMI. Если HMI сторонняя (OPC UA) — достаточно программного модуля + Symbol Configuration.

**[LOW]** **AM-6. Для ООП-проектов оцените Object Oriented Alarming Library** (ControlSphere, CODESYS Store): FB сам создаёт и активирует свои аварии через возможности Alarm Manager — не нужно вручную вести списки аварий отдельно от кода (CODESYS Store, OOA Library([store.codesys.com](https://store.codesys.com/en/catalogsearch/result/index/?cat=4&q=oscat+libraries))).

---

---

## 10. Качество: Git, статический анализ, тесты, ревью

**[HIGH]** **Q-1. Проект — в Git.** CODESYS Git (входит в CODESYS Professional Developer Edition) даёт нативное версионирование всех объектов приложения (CODESYS Store, CODESYS Git([store.codesys.com](https://store.codesys.com/en/catalogsearch/result/index/?p=2&q=codesys+function))). Минимум без него: регулярный экспорт в PLCopen XML / .export + внешний Git.

**[HIGH]** **Q-2. Static Analysis перед каждым коммитом.** Встроенный CODESYS Static Analysis проверяет правила именования, неиспользуемые переменные, недостижимый код, границы массивов. Агент обязан прогонять и устранять findings уровня Error; Warning — по возможности.

**[HIGH]** **Q-3. Компиляция + симуляция обязательны.** Ни один FB не считается готовым без прогона в CODESYS Simulation: принудительные фронты входов, проверка переходов состояний, таймаутов и порогов. Сгенерированный ST-код — это стартовая точка, которая должна быть скомпилирована и протестирована в целевом проекте (CODESYS Help, Programming in ST([helpme-codesys.com](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_programming_in_st.html))).

**[MED]** **Q-4. Юнит-тесты для библиотек.** Для пользовательских библиотек — CODESYS Test Manager или фреймворк юнит-тестов (например, TcUnit/CfUnit-подход): тест на каждый переход состояния и каждый граничный случай.

**[MED]** **Q-5. Symbol Configuration — явный контракт наружу.** Наружу (OPC UA/SCADA) экспортируются только переменные, помеченные `{attribute 'symbol' := 'readwrite'}` / `'read'` — не вся GVL (mcptoolkit-for-codesys docs: 2026-05-26([lobehub.com](https://lobehub.com/mcp/zbest1000-mcptoolkit-for-codesys))).

**[MED]** **Q-6. Code review по чек-листу.** Профессиональные чек-листы включают: согласованные имена, иерархическая структура, IEC 61131-3, alarm management, Git, симуляция, документация заголовков FB (Prybisch Automation: 2025-09-20([prybisch-automation.eu](https://prybisch-automation.eu/en/blog/plc-programming-best-practices))).

**[LOW]** **Q-7. Избегайте устаревших возможностей.** PLCopen CP27: никаких JUMP, BCD-инструкций, практик 2-й редакции IEC, избыточных глобалов (PLCopen Coding Guidelines, Rule CP27: 2016-04-20).

---

## 11. Чек-лист агента перед и во время разработки

Агент, приступающий к задаче в CODESYS-проекте, обязан пройти этот список. Пропуск пункта = явно зафиксированный риск.

### 11.1. Перед написанием кода

1. **Цель известна точно:** контроллер (модель, рантайм, версия CODESYS/IDE), объём памяти, целевой цикл MainTask. Код под embedded-контроллер с 1 МБ и под Control Win — разный код (длины строк, размеры массивов, LREAL vs REAL).
2. **Прочитаны действующие стандарты проекта:** GVL, DUT, существующие FB, соглашение имён. Новый код наследует стиль проекта, а не приносит свой.
3. **Установленные библиотеки и их версии проверены в Library Manager** — API блоков сверено по факту, не по памяти (правило L-4).
4. **Есть ли готовое в MachineLib/библиотеках проекта?** Дублирование существующего FB — дефект.
5. **Понятна модель состояний машины** (PackML или проектная): к какому состоянию относится новая логика, что происходит при Abort/Stop/Hold.

### 11.2. Во время разработки

1. Тип POU выбран осознанно (раздел 3.1); всё с состоянием — FUNCTION_BLOCK.
2. Инкапсуляция: внутреннее в VAR; снаружи только VAR_INPUT/VAR_OUTPUT/METHOD/PROPERTY (OOP-1). Нет VAR_EXTERNAL и прямых обращений к GVL из FB (OOP-2).
3. Действия во времени — по шаблону PLCopen Execute/Done/Busy/Error/ErrorID (раздел 4); статусы взаимоисключаемы.
4. Именование по разделу 5; локальные счётчики циклов — с подчёркиванием (`_i`); нет затенения глобалов (N-2).
5. Циклы FOR по массивам — всегда с проверкой границ (`LIMIT`, `LOWER_BOUND/UPPER_BOUND`); нет WHILE с непредсказуемым выходом (S2-5).
6. Все таймеры и дочерние FB вызываются каждый скан (не «только когда нужно») — иначе они не считают.
7. Ошибки формируются как биты-триггеры в Alarm Manager / FB_AlarmManager с текстом «проблема + место + действие» (AM-3); у каждой ошибки есть код (ErrorID).
8. Каждая ошибка имеет путь восстановления: квитирование, Reset, переход в безопасное состояние. Состояние Clearing — шина сброса.
9. Код fail-safe по умолчанию: обрыв Н.З. цепи выглядит как авария, а не как «всё тихо»; при потере связи (NVL heartbeat) — безопасное состояние.
10. Комментарии объясняют намерение и временны́е допущения («почему», не «что»).

### 11.3. Перед сдачей

1. Компиляция без ошибок; Static Analysis — ноль Error, warnings разобраны (Q-2).
2. Симуляция: переходы состояний, таймауты, залипания, обрывы прогнаны принудительно (Q-3).
3. Retain/persistent-раскладка не изменилась без предупреждения пользователя (RP-2).
4. Изменения закоммичены; сообщение коммита объясняет зачем, а не что.
5. Документация/заголовки FB обновлены; список аварий синхронизирован с текстами для HMI.
6. Online change vs download: агент явно пишет пользователю, что потребуется (online change безопасен для логики; изменение retain/интерфейсов библиотек — download с остановом).

> **Важно.** **Границы агента:** safety-функции (SIL/PL), motion на реальных осях, параметры ПИД на объекте — агент готовит код и симуляцию, но ввод в эксплуатацию только после проверки инженером и, где требуется, по результатам оценки рисков. Программная диагностика не заменяет аппаратные цепи безопасности.

---

---

## 13. Источники

| Источник | Что взято | Ссылка |
|---|---|---|
| PLCopen Coding Guidelines v1.0 (2016-04-20) | Правила именования N1–N10, CP5/CP6/CP27, L14, E2, C5 | [plcopen.org](https://www.plcopen.org/download_file/force/ff60e817-eee5-442d-b718-a357a7279c7e/342/) |
| CODESYS Online Help / helpme-codesys | GVL, Task Configuration, NVL, интерфейсы, библиотеки, ST | [helpme-codesys.com](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_f_task_configuration.html) • [help.codesys.com](https://help.codesys.com/api-content/2/codesys/3.5.13.0/en/_cds_obj_gvl/) |
| Bosch Rexroth ctrlX Community (2026-01-13) | Пошаговая настройка Alarm Manager | [community.boschrexroth.com](https://community.boschrexroth.com/ctrlx-automation-how-tos-qmglrz33/post/how-to-use-the-alarm-management-from-codesys-V12Q2qWs1v4KWkU) |
| PLC BLOG | Классы аварий, методы квитирования, Alarm Storage | [plcblog.in](https://plcblog.in/plc/codesys/CODESYS%20Alarm%20Management%20and%20configuration.php) |
| Zenn (2025-03-28) | Разбор Example Project Alarm Manager, latch-переменные | [zenn.dev](https://zenn.dev/kzchd/articles/06bb7ff4b35e62) |
| Prybisch Automation (2025-09-20) | Префиксы ix/qx, чек-лист проекта, NAMUR NE 107 | [prybisch-automation.eu](https://prybisch-automation.eu/en/blog/plc-programming-best-practices) |
| Industrial Monitor Direct (2026-04-04 / 2026-07-12) | Иерархия задач, cyclic vs freewheeling; OSCAT install и CVE | [industrialmonitordirect.com](https://industrialmonitordirect.com/blogs/knowledgebase/codesys-cyclic-vs-freewheeling-task-configuration-best-practices) |
| Weintek USA forum (2024-12-10) | Приоритеты задач, запас ×2–3 по времени, watchdog | [forum.weintekusa.com](https://forum.weintekusa.com/t/how-to-optimize-task-management-in-codesys/2560) |
| CODESYS Forge (2015–2018) | qualified_only, ООП-паттерны (REFERENCE TO, FB_INIT, свойства), защита библиотек | [forge.codesys.com](https://forge.codesys.com/forge/talk/Engineering/thread/49f235f440/) |
| WAGO Community (2023-09-11) | NVL heartbeat, лимиты NVL | [wago.community](https://www.wago.community/t/best-solution-for-two-way-communication/590) |
| Yaskawa AN.MPIEC.01 / ICP DAS PLCopen manual | Execute/Enable-модели, взаимоисключаемые выходы | [yaskawa.com](https://www.yaskawa.com/delegate/getAttachment?documentId=AN.MWIEC.01&cmd=documents&documentName=AN.MPIEC.01%20Creating%20PLCopen%20Compliant%20function%20blocks.pdf) |
| Motion Control Tips (2019-08-26) / Eclipse OSCAT | Состав и ценность OSCAT | [motioncontroltips.com](https://www.motioncontroltips.com/what-are-oscat-files-how-do-they-relate-to-codesys/) |
| CODESYS Store | CODESYS Git, OOA Library, MQTT, OSCAT в Store | [store.codesys.com](https://store.codesys.com/) |
| АИП (2019-02-20) | Параметры VisuTask (200–400 мс, prio 31) | [aip.com.ru](https://aip.com.ru/article/vizualizatsiya_v_srede_codesys) |
| codesys-mcp writing guidance | Выбор типа POU, проверка библиотек в Library Manager, компиляция в целевом проекте | плагин codesys-mcp (локально) |

---
