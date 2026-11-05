# Правило 08. MachineLib — база знаний (полный структурированный список)

Эталонная «библиотека как документация»: полный состав элементов MachineLib —
DUT, FB, PROGRAM, GVL, матрица зависимостей, соглашения об именовании.
Использовать как источник идей/паттернов при проектировании (см. docs/01,
порядок поиска решения). Файл перенесён из монолита AGENTS.md без изменений.

---

# ГЛАВА 4. MachineLib — полный структурированный список элементов

# MachineLib — полный структурированный список элементов
Источник: документация MachineLib (сторонний продукт; конвертирована в markdown при подготовке этого репозитория).

## Состав библиотеки (сводка)

- DUT (все — перечисления, объявлены в `MachineLib :: DUT_Common`): **E_PackMLState, E_PackMLCommand, E_LightMode, E_PanelMode, E_CylSensors** — 5 шт. Структур (STRUCT) в документе НЕТ.
- FUNCTION_BLOCK: **13 шт.** — FB_Blinker, FB_PackML, FB_TowerLight, FB_OperatorButtons, FB_PneumoCylinder, FB_SensorStuck, FB_ButtonStuck, FB_SafetyMonitor, FB_AlarmManager, FB_CycleTimeAnalyzer, FB_FirstFault, FB_EventLogger, FB_Heartbeat, FB_ProductionStats.
- FUNCTION (FUN): **нет**.
- PROGRAM: **PRG_Machine** (пример интеграции).
- GVL: **нет**; единственная константа — `RESERVED_FROM : INT := 48` внутри `VAR CONSTANT` блока FB_AlarmManager.

---

## 1. DUT — перечисления (группа DUT_Common)

### 1.1. E_PackMLState — DUT (ENUM) — PackML: ДА (состояния машины)
17 состояний ISA-TR88: коды 1..10 — действующие (acting), 11..17 — ожидающие (wait). Дословная сигнатура:

```iecst
TYPE E_PackMLState :
(
    // --- Действующие (acting) ---
    Aborting     := 1,   // Аварийная остановка (выполнение)
    Clearing     := 2,   // Сброс ошибок после Abort/Stop
    Stopping     := 3,   // Штатная остановка (выполнение)
    Resetting    := 4,   // Инициализация / приведение в исходное
    Starting     := 5,   // Запуск (выполнение)
    Suspending   := 6,   // Переход в паузу (выполнение)
    Unsuspending := 7,   // Выход из паузы (выполнение)
    Holding      := 8,   // Удержание / доведение до точки паузы
    Unholding    := 9,   // Выход из удержания
    Completing   := 10,  // Завершение цикла
    // --- Ожидающие (wait) ---
    Aborted      := 11,  // Аварийно остановлен
    Stopped      := 12,  // Остановлен
    Idle         := 13,  // Готов к работе
    Execute      := 14,  // РАБОТА (основное состояние)
    Suspended    := 15,  // Пауза (ожидание действия оператора)
    Held         := 16,  // Удержан
    Complete     := 17   // Цикл завершён
);
END_TYPE
```
Важно: acting-состояния имеют коды 1..10, поэтому проверка `eState < E_PackMLState.Aborted` = «состояние действующее».

### 1.2. E_PackMLCommand — DUT (ENUM) — PackML: ДА (команды)
```iecst
TYPE E_PackMLCommand :
(
    None      := 0,
    Reset     := 1,   // Idle ← Complete/Stopped; инициализация
    Start     := 2,   // Запуск из Idle
    Stop      := 3,   // Штатная остановка с завершением цикла
    Hold      := 4,   // Удержание (временная пауза цикла)
    Unhold    := 5,
    Suspend   := 6,   // Пауза до действия оператора
    Unsuspend := 7,
    Abort     := 8,   // Аварийная немедленная остановка
    Clear     := 9    // Сброс из Aborted/Stopped
);
END_TYPE
```

### 1.3. E_LightMode — DUT (ENUM) — PackML: нет (режимы каналов светофора)
```iecst
TYPE E_LightMode :
(
    Off       := 0,   // Погашен
    On        := 1,   // Постоянное свечение
    BlinkSlow := 2,   // Медленное мигание (1 Гц)
    BlinkFast := 3    // Быстрое мигание (4 Гц)
);
END_TYPE
```

### 1.4. E_PanelMode — DUT (ENUM) — PackML: косвенно (конфигурация панели оператора)
```iecst
TYPE E_PanelMode :
(
    StartStopToggle   := 0,  // Одна кнопка Пуск/Стоп (триггер)
    StartStopSeparate := 1,  // Раздельные Пуск и Стоп
    StartStopAction   := 2   // Пуск/Стоп + кнопка Действие + Пауза
);
END_TYPE
```

### 1.5. E_CylSensors — DUT (ENUM) — PackML: нет (конфигурация герконов пневмоцилиндра)
```iecst
TYPE E_CylSensors :
(
    StartOnly   := 1,  // 1 геркон: начальное положение
    StartEnd    := 2,  // 2 геркона: начальное + конечное
    StartMidEnd := 3   // 3 геркона: начальное + среднее + конечное
);
END_TYPE
```

---

## 2. Функциональные блоки (FB)

### 2.0. FB_Blinker — FB — PackML: нет (вспомогательный)
Единый генератор мигания (меандры 1 Гц и 4 Гц) для светофора и подсветки кнопок. Один экземпляр на программу. Два классических генератора на парах TON.

Интерфейс:
```iecst
VAR_INPUT
    bEnable : BOOL := TRUE;
    tSlow   : TIME := T#500ms;  // полупериод медленного мигания (1 Гц)
    tFast   : TIME := T#125ms;  // полупериод быстрого мигания (4 Гц)
END_VAR
VAR_OUTPUT
    bSlow   : BOOL;             // меандр 1 Гц
    bFast   : BOOL;             // меандр 4 Гц
END_VAR
```
Внутренние: `_tonSlow1, _tonSlow2 : TON; _tonFast1, _tonFast2 : TON;` (генератор на двух TON). Методов/свойств нет.

---

### 2.1. FB_PackML — FB — PackML: ДА (ЯДРО, машина состояний ISA-TR88/OMAC)
Машина состояний: 17 состояний, 9 команд. Действующие состояния завершаются вызовом `M_ActorDone()` прикладной программой; любое действующее состояние защищено таймаутом `tStateTimeout` → переход в Aborting. Команда Abort имеет абсолютный приоритет из любого состояния (кроме Aborted/Aborting).

Интерфейс (дословно):
```iecst
VAR_INPUT
    bEnable        : BOOL := TRUE;
    tStateTimeout  : TIME := T#30s;
    bUseHold       : BOOL := TRUE;   // конфигурация: ветка Hold разрешена
    bUseSuspend    : BOOL := TRUE;   // конфигурация: ветка Suspend разрешена
END_VAR
VAR_OUTPUT
    eState         : E_PackMLState := E_PackMLState.Stopped;
    eStatePrev     : E_PackMLState;
    bError         : BOOL;
    nErrorID       : INT;            // 1=таймаут состояния, 2=недопустимая команда
END_VAR
VAR
    _eCmd          : E_PackMLCommand;
    _bCmdPending   : BOOL;
    _bActorDone    : BOOL;
    _tonState      : TON;
    _bEntered      : BOOL;           // импульс входа в состояние (аналог StateChanged, внутренний, сбрасывается в конце цикла)
END_VAR
```

Методы:
| Метод | Сигнатура | Назначение |
|---|---|---|
| M_Command | `METHOD M_Command : BOOL` / `VAR_INPUT eCmd : E_PackMLCommand; END_VAR` | Подать команду (импульсная, хранится до обработки мин. 1 цикл); TRUE если команда принята (не было ожидающей) |
| M_ActorDone | `METHOD M_ActorDone` (без параметров) | Прикладная программа сообщает: действующее состояние завершено (`_bActorDone := TRUE`) |
| M_IsActing | `METHOD M_IsActing : BOOL` | TRUE, если состояние действующее: `M_IsActing := eState < E_PackMLState.Aborted;` |
| _TakeCmd | `METHOD PRIVATE _TakeCmd : BOOL` / `VAR_INPUT eCmd : E_PackMLCommand; END_VAR` | Внутренний: забрать ожидающую команду, если совпадает |
| _SetState | `METHOD PRIVATE _SetState` / `VAR_INPUT eNew : E_PackMLState; END_VAR` | Внутренний: переход с фиксацией eStatePrev, взводит `_bEntered`, сбрасывает таймер таймаута |

Свойства (PROPERTY, все GET-only):
| Свойство | Тип | Значение |
|---|---|---|
| P_StateText | STRING(20) | Русское имя состояния для HMI (CASE по всем 17 состояниям: 'Аварийная остановка', 'Аварийно остановлен', 'Сброс', 'Остановка', 'Остановлен', 'Инициализация', 'Готов к работе', 'Запуск', 'Работа', 'Переход в паузу', 'Пауза', 'Выход из паузы', 'Удержание', 'Удержан', 'Возврат в работу', 'Завершение цикла', 'Цикл завершён') |
| P_IsExecute | BOOL | `eState = E_PackMLState.Execute` |
| P_IsIdle | BOOL | `eState = E_PackMLState.Idle` |
| P_IsAborted | BOOL | `eState = E_PackMLState.Aborted OR eState = E_PackMLState.Aborting` |

Граф переходов (дословно из документа):
- Idle --Start--> Starting --done--> Execute
- Execute --Stop--> Stopping; --Hold--> Holding (если bUseHold); --Suspend--> Suspending (если bUseSuspend); --done--> Completing
- Completing --done--> Complete; Complete --Reset--> Resetting; Resetting --done--> Idle
- Holding --done--> Held; Held --Unhold--> Unholding, --Stop--> Stopping; Unholding --done--> Execute
- Suspending --done--> Suspended; Suspended --Unsuspend--> Unsuspending, --Stop--> Stopping; Unsuspending --done--> Execute
- Stopping --done--> Stopped; Stopped --Clear--> Clearing, --Reset--> Resetting
- Aborting --done--> Aborted; Aborted --Clear--> Clearing
- Clearing: сбрасывает bError/nErrorID, --done--> Stopped
- Abort: из любого состояния (кроме Aborted/Aborting) -> Aborting
- Таймаут любого acting-состояния: bError:=TRUE, nErrorID:=1, переход в Aborting
- В конце цикла сбрасываются `_bActorDone` и `_bEntered`

Зависимости: использует E_PackMLState, E_PackMLCommand, TON. Потребители: FB_TowerLight, FB_OperatorButtons, FB_SafetyMonitor, FB_AlarmManager, PRG_Machine, диагностика (9.x).

---

### 2.2. FB_TowerLight — FB — PackML: ДА (индикация по состоянию машины)
Светофор 5 каналов (зелёный/красный/жёлтый/синий/зуммер). Режим канала = 2 бита (E_LightMode); конфигурация одного состояния = один WORD; все 17 состояний = `ARRAY[E_PackMLState] OF WORD`. Жёстко привязан к eState от FB_PackML.

Карта битов WORD: 0..1 — зелёный; 2..3 — красный; 4..5 — жёлтый; 6..7 — синий; 8..9 — зуммер; 10..15 — резерв. Значения: 00 выкл, 01 постоянно, 10 мигание 1 Гц, 11 мигание 4 Гц.

Интерфейс:
```iecst
VAR_INPUT
    eState      : E_PackMLState;    // состояние от FB_PackML
    bBlinkSlow  : BOOL;             // меандр 1 Гц от FB_Blinker
    bBlinkFast  : BOOL;             // меандр 4 Гц от FB_Blinker
    bMuteBuzzer : BOOL;             // квитирование зуммера (лампы продолжают работать)
END_VAR
VAR_OUTPUT
    Q_Green     : BOOL;
    Q_Red       : BOOL;
    Q_Yellow    : BOOL;
    Q_Blue      : BOOL;
    Q_Buzzer    : BOOL;
END_VAR
VAR
    _aConfig    : ARRAY[E_PackMLState] OF WORD;  // конфигурация: WORD на состояние
    _wActive    : WORD;
    _bInitDone  : BOOL;
END_VAR
```

Методы:
| Метод | Сигнатура | Назначение |
|---|---|---|
| _Channel | `METHOD PRIVATE _Channel : BOOL` / `VAR_INPUT wCfg : WORD; nShift : INT; bSlow : BOOL; bFast : BOOL; END_VAR` | Распаковка 2-битного режима канала: `eMode := E_LightMode((WORD_TO_DWORD(wCfg) SHR nShift) AND 16#3);` + CASE по E_LightMode |
| M_SetStateConfig | `METHOD M_SetStateConfig` / `VAR_INPUT eSt : E_PackMLState; eGreen, eRed, eYellow, eBlue, eBuzzer : E_LightMode; END_VAR` | Настройка одного состояния: упаковка 5 режимов в WORD со сдвигами SHL 0/2/4/6/8 |
| M_LoadDefaults | `METHOD M_LoadDefaults` (без параметров) | Загрузка таблицы по умолчанию (вызывается однократно при первом цикле) |

Таблица по умолчанию (рекомендация PackML), дословные вызовы:
```iecst
M_SetStateConfig(E_PackMLState.Execute,      On,        Off, Off,       Off, Off);
M_SetStateConfig(E_PackMLState.Idle,         BlinkSlow, Off, Off,       Off, Off);
M_SetStateConfig(E_PackMLState.Starting,     BlinkFast, Off, Off,       Off, Off);
M_SetStateConfig(E_PackMLState.Resetting,    BlinkFast, Off, Off,       Off, Off);
M_SetStateConfig(E_PackMLState.Completing,   BlinkFast, Off, Off,       Off, Off);
M_SetStateConfig(E_PackMLState.Holding,      Off, Off, Off, BlinkSlow, Off, Off);
M_SetStateConfig(E_PackMLState.Held,         Off, Off, Off, On,        Off, Off);
M_SetStateConfig(E_PackMLState.Unholding,    Off, Off, Off, BlinkFast, Off, Off);
M_SetStateConfig(E_PackMLState.Suspending,   Off, Off, Off, Off, BlinkSlow, Off);
M_SetStateConfig(E_PackMLState.Suspended,    Off, Off, Off, Off, On,        Off);
M_SetStateConfig(E_PackMLState.Unsuspending, Off, Off, Off, Off, BlinkFast, Off);
M_SetStateConfig(E_PackMLState.Stopping,     Off, Off, Off, BlinkSlow, Off, Off);
M_SetStateConfig(E_PackMLState.Clearing,     Off, Off, Off, BlinkSlow, Off, Off);
M_SetStateConfig(E_PackMLState.Aborting,     Off, BlinkFast, Off, Off, On);
M_SetStateConfig(E_PackMLState.Aborted,      Off, On,        Off, Off, BlinkSlow);
M_SetStateConfig(E_PackMLState.Stopped,      Off, Off, Off, Off, Off);
M_SetStateConfig(E_PackMLState.Complete,     Off, Off, Off, Off, Off);
```
Зависимости: входы от FB_PackML (eState) и FB_Blinker (bSlow/bFast); типы E_PackMLState, E_LightMode.

---

### 2.3. FB_OperatorButtons — FB — PackML: ДА (источник команд машины)
Кнопки оператора с подсветкой. 3 режима панели (E_PanelMode), нормализация Н.О./Н.З. контактов, длинное удержание «Стоп» (>= tLongStop) = Abort, квитирование действия 3x100 мс. Fail-safe: обрыв Н.З. «Стоп» выглядит как нажатие.

Интерфейс (дословно):
```iecst
VAR_INPUT
    // --- Физические входы (сырые сигналы) ---
    bStartRaw        : BOOL;
    bStopRaw         : BOOL;
    bActionRaw       : BOOL;
    bPauseRaw        : BOOL;
    // --- Конфигурация типа контактов ---
    bStartNO         : BOOL := TRUE;   // TRUE = Н.О., FALSE = Н.З.
    bStopNC          : BOOL := TRUE;   // TRUE = Н.З.
    bActionNO        : BOOL := TRUE;
    bPauseNC         : BOOL := TRUE;
    // --- Конфигурация панели ---
    eMode            : E_PanelMode := E_PanelMode.StartStopAction;
    tLongStop        : TIME := T#3s;     // удержание для Abort
    tAckBlink        : TIME := T#100ms;  // длительность одного подмигивания
    nAckCount        : INT := 3;         // количество подмигиваний
    // --- Связь с машиной состояний ---
    eState           : E_PackMLState;
    bActionRequired  : BOOL;             // от процесса: требуется действие оператора
    bBlinkSlow       : BOOL;
    bBlinkFast       : BOOL;
END_VAR
VAR_OUTPUT
    // --- Подсветка ---
    Q_LampGreen      : BOOL;
    Q_LampRed        : BOOL;
    Q_LampBlue       : BOOL;
    Q_LampYellow     : BOOL;
    // --- Команды к FB_PackML ---
    eCmd             : E_PackMLCommand;
    bCmdPulse        : BOOL;             // 1 цикл: команда eCmd действительна
    // --- Квитирование действия ---
    bActionAck       : BOOL;             // 1 цикл: оператор подтвердил действие
    // --- Нормализованные состояния кнопок (для FB_ButtonStuck) ---
    bStartPressed    : BOOL;
    bStopPressed     : BOOL;
    bActionPressed   : BOOL;
    bPausePressed    : BOOL;
END_VAR
VAR
    _rStart, _rAction, _rPause : R_TRIG;
    _fStop                     : F_TRIG;
    _tonLongStop               : TON;
    _bToggleRun                : BOOL;   // для режима StartStopToggle
    _nAckStep                  : INT;    // автомат квитирования: 0=нет, 1..n*2 = фазы вкл/выкл
    _tonAck                    : TON;
    _bAckLamp                  : BOOL;
END_VAR
```

Нормализация контактов (дословно):
```iecst
bStartPressed  := bStartRaw  XOR NOT bStartNO;
bStopPressed   := bStopRaw   XOR bStopNC;
bActionPressed := bActionRaw XOR NOT bActionNO;
bPausePressed  := bPauseRaw  XOR bPauseNC;
```

Логика команд:
- ПУСК (фронт bStartPressed): режим StartStopToggle — Idle->Start / Execute->Stop; иначе — Idle->Start, Complete/Stopped->Reset.
- СТОП: `_tonLongStop.Q` (удержание >= tLongStop) -> Abort (приоритет); отпускание раньше (`_fStop.Q AND NOT _tonLongStop.Q`) -> из Execute/Held/Suspended команда Stop; из Aborted/Stopped — Clear.
- ДЕЙСТВИЕ: при bActionRequired -> bActionAck (1 цикл) + запуск автомата 3x100 мс подмигивания синей лампы; иначе из Suspended -> Unsuspend.
- ПАУЗА: из Execute -> Hold; из Held -> Unhold.

Логика подсветки:
- Q_LampGreen: Idle -> bBlinkSlow (мигает = готов); Execute -> TRUE; иначе FALSE.
- Q_LampRed: Aborted -> bBlinkFast; любое acting (`eState < E_PackMLState.Aborted`) -> TRUE; иначе FALSE.
- Q_LampBlue: квитирование (_nAckStep>0) -> _bAckLamp; bActionRequired -> bBlinkFast; Suspended -> TRUE; иначе FALSE.
- Q_LampYellow: Holding -> bBlinkSlow; Held -> TRUE; иначе FALSE.

Зависимости: FB_PackML (eState вход, eCmd/bCmdPulse выход), FB_Blinker, E_PanelMode, E_PackMLCommand; потребители выходов — FB_ButtonStuck (bXxxPressed), FB_SafetyMonitor (bStartAttempt).

---

### 2.4. FB_PneumoCylinder — FB — PackML: нет (автономная диагностика)
Контроль перемещения пневмоцилиндра «от геркона до геркона» с самообучением порогов (скользящее среднее по окну из 10 измерений x rMargin). Не управляет клапаном — только наблюдает за командой и герконами. Конфигурации 1/2/3 геркона (E_CylSensors). Переобучение каждые nLearnCycles циклов. Bypass.

Интерфейс (дословно):
```iecst
VAR_INPUT
    bCmdExtend   : BOOL;
    bSenStart    : BOOL;
    bSenMid      : BOOL;
    bSenEnd      : BOOL;
    bBypass      : BOOL;              // 1 = контроль отключён
    bReset       : BOOL;
    eSensors     : E_CylSensors := E_CylSensors.StartEnd;
    nLearnCycles : INT := 100;
    rMargin      : REAL := 1.3;
    tMaxStroke   : TIME := T#10s;
END_VAR
VAR_OUTPUT
    bError       : BOOL;
    bLearning    : BOOL;
    tLimitExt    : TIME;
    tLimitRet    : TIME;
    nCycleCount  : DINT;
END_VAR
VAR
    _nPhase      : INT;               // 0=ожидание, 1=выдв.:уход из нач., 2=выдв.:к среднему, 3=выдв.:к конечному, 4=втяг.:к начальному
    _tonMove     : TON;
    _tMoveStart  : TIME;
    _bCmdPrev    : BOOL;
    _liSumExt, _liSumRet : LREAL;     // статистика обучения (скользящее среднее)
    _nStatExt, _nStatRet : INT;
    _tAvgExt, _tAvgRet   : TIME;
END_VAR
```

Методы (все PRIVATE):
| Метод | Назначение |
|---|---|
| _LearnExt | Учёт измерения выдвижения: `liMs := TIME_TO_LREAL(_tonMove.ET);` окно 10 измерений, затем `tLimitExt := LREAL_TO_TIME(TIME_TO_LREAL(_tAvgExt) * rMargin);` |
| _LearnRet | То же для втягивания -> tLimitRet |
| _CheckRelearn | При `nCycleCount >= nLearnCycles`: обнуляет счётчик и статистику (пороги не обнуляются до пересчёта новой выборки) |

Логика: автомат фаз 0..4; таймаут `_tonMove.Q` -> bError:=TRUE; `bLearning := tLimitExt = T#0s OR tLimitRet = T#0s;`. Рекомендация: массив `aCyl : ARRAY[1..8] OF FB_PneumoCylinder;`, ошибки — в FB_AlarmManager (ID 3..10).

Зависимости: E_CylSensors, TON. Потребитель: FB_AlarmManager.

---

### 2.5. FB_SensorStuck — FB — PackML: нет
Контроль залипания/длительного засвета датчика. Скользящая кольцевая выборка длительностей засвета (nWindow, 1..32); порог = среднее x rSensitivity; при превышении: bStuck (пока засвечен) + bError (защёлкнут до bReset); во время ошибки выборка не пополняется.

Интерфейс:
```iecst
VAR_INPUT
    bSensor      : BOOL;
    bEnable      : BOOL;              // флаг включения контроля
    bReset       : BOOL;              // сброс ошибки
    nWindow      : INT := 10;         // размер скользящей выборки (1..32)
    rSensitivity : REAL := 3.0;       // чувствительность: среднее x n% (3.0 = 300%)
    tMinValid    : TIME := T#5ms;     // засветы короче — в выборку не берём (дребезг)
END_VAR
VAR_OUTPUT
    bStuck       : BOOL;              // = 1 пока датчик залип (засвечен сверх нормы)
    bError       : BOOL;              // защёлкнутая ошибка до bReset
    tAvg         : TIME;              // текущее среднее засвета
    nSamples     : INT;               // накоплено измерений
END_VAR
VAR
    _tonOn       : TON;
    _fSensor     : F_TRIG;
    _aBuf        : ARRAY[1..32] OF LREAL;  // кольцевой буфер, мс
    _nHead       : INT := 1;
    _nCount      : INT;
    _liSum       : LREAL;
    _tLimit      : TIME;
    _i           : INT;
END_VAR
```
Измерение: `_tonOn(IN := bSensor AND bEnable, PT := T#24h);` выборка по заднему фронту; `_tLimit := LREAL_TO_TIME(TIME_TO_LREAL(tAvg) * rSensitivity);`. Ошибки — в FB_AlarmManager (ID 11..18).

---

### 2.6. FB_ButtonStuck — FB — PackML: косвенно (работает на входах модуля кнопок)
Контроль залипания кнопок: любая кнопка нажата дольше tStuckTime -> залипание. Конфигурационная инверсия для Н.З. контактов. Может брать нормализованные bXxxPressed из FB_OperatorButtons (инверсия уже учтена).

Интерфейс:
```iecst
VAR_INPUT
    aButtons   : ARRAY[1..16] OF BOOL;   // сырые входы кнопок
    aInvert    : ARRAY[1..16] OF BOOL;   // конфигурация: TRUE = контакт Н.З.
    nCount     : INT := 4;               // сколько кнопок контролируем (1..16)
    tStuckTime : TIME := T#5s;           // порог залипания
    bReset     : BOOL;
END_VAR
VAR_OUTPUT
    bError     : BOOL;                   // хотя бы одна кнопка залипла
    aStuck     : ARRAY[1..16] OF BOOL;   // побитовая карта залипших кнопок
    nFirstIndex: INT;                    // индекс первой залипшей (0 = нет)
END_VAR
VAR
    _aTon      : ARRAY[1..16] OF TON;
    _aPressed  : ARRAY[1..16] OF BOOL;
    _i         : INT;
END_VAR
```
Ядро: `_aPressed[_i] := aButtons[_i] XOR aInvert[_i]; aStuck[_i] := _aTon[_i].Q AND _aPressed[_i];`. Ошибка не защёлкивается — уходит при отпускании (для защёлки — через FB_AlarmManager, авария ID 2).

---

### 2.7. FB_SafetyMonitor — FB — PackML: ДА (источник команды Abort)
Контроль обрыва аварийных цепей (двери, грибки — все Н.З., норма = 1). НЕОТКЛЮЧАЕМЫЙ (намеренно нет bEnable/bBypass — проектное ограничение безопасности). Не заменяет аппаратное реле безопасности (SIL/PL).

Поведение:
- Обрыв при работающем оборудовании (bMachineRunning) -> bCmdAbort (машина -> Aborting).
- Обрыв при неработающем -> только bWarning.
- Попытка запуска при обрыве -> импульс bStartDenied на tDenyPulse («Запуск запрещён»).

Интерфейс:
```iecst
VAR_INPUT
    aSignals        : ARRAY[1..32] OF BOOL;  // аварийные цепи: двери, грибки (норма = 1)
    nCount          : INT := 1;              // количество контролируемых цепей (1..32)
    bMachineRunning : BOOL;                  // от FB_PackML: Execute или acting
    bStartAttempt   : BOOL;                  // импульс попытки запуска (от модуля 3 / HMI)
    tDenyPulse      : TIME := T#3s;          // длительность бита "запуск запрещён"
    bReset          : BOOL;                  // квитирование после восстановления цепи
END_VAR
VAR_OUTPUT
    bChainOk      : BOOL;                    // все цепи замкнуты
    bFault        : BOOL;                    // обрыв (защёлкнут до bReset)
    nFaultIndex   : INT;                     // номер первой разомкнутой цепи
    bWarning      : BOOL;                    // обрыв при неработающем оборудовании
    bCmdAbort     : BOOL;                    // команда Abort к FB_PackML
    bStartDenied  : BOOL;                    // импульс tDenyPulse: запуск запрещён
END_VAR
VAR
    _i            : INT;
    _bBreakNow    : BOOL;
    _rStartAtt    : R_TRIG;
    _tonDeny      : TON;
END_VAR
```
Фиксирует первую разомкнутую цепь (приоритет первого обрыва); сброс защёлки: `bReset AND NOT _bBreakNow`. Подключение: `bMachineRunning := fbPackML.P_IsExecute OR fbPackML.M_IsActing();`, bCmdAbort -> `fbPackML.M_Command(E_PackMLCommand.Abort)`.

Зависимости: FB_PackML (вход состояния, выход Abort), FB_OperatorButtons (bStartAttempt), FB_AlarmManager (bFault -> авария ID 1).

---

### 2.8. FB_AlarmManager — FB — PackML: косвенно (авария 0 = таймаут состояния FB_PackML)
Централизованный менеджер аварий: 64 бита + строковые сообщения STRING(80) для HMI. Диапазон 0..47 — системные аварии библиотеки, 48..63 — резерв разработчика. Защёлка по переднему фронту триггеров; квитирование (bAck) снимает только аварии, чей источник ушёл.

Константа (единственная в библиотеке, внутри FB):
```iecst
VAR CONSTANT
    RESERVED_FROM : INT := 48;          // 48..63 — резерв разработчика
END_VAR
```

Интерфейс:
```iecst
VAR_INPUT
    aTriggers : ARRAY[0..63] OF BOOL;  // входы-ошибки от модулей (фронт = новая авария)
    bAck      : BOOL;                  // квитировать все
END_VAR
VAR_OUTPUT
    aActive   : ARRAY[0..63] OF BOOL;  // активные аварии (битовый массив)
    bAnyActive: BOOL;
    nActiveCount : INT;
END_VAR
VAR
    _aTrigPrev : ARRAY[0..63] OF BOOL;
    _aText     : ARRAY[0..63] OF STRING(80);
    _bInitDone : BOOL;
    _i         : INT;
END_VAR
```

Методы:
| Метод | Сигнатура | Назначение |
|---|---|---|
| M_Raise | `METHOD M_Raise` / `VAR_INPUT nID : INT; sText : STRING(80); END_VAR` | Программная постановка аварии с текстом (0..63) |
| M_Clear | `METHOD M_Clear` / `VAR_INPUT nID : INT; END_VAR` | Снять конкретную аварию |
| M_GetText | `METHOD M_GetText : STRING(80)` / `VAR_INPUT nID : INT; END_VAR` | Текст аварии для HMI |
| M_FirstActive | `METHOD M_FirstActive : INT` | ID первой активной аварии (-1 = нет) |
| M_SetText | `METHOD M_SetText` / `VAR_INPUT nID : INT; sText : STRING(80); END_VAR` | Смена текста (локализация) |
| M_LoadDefaultTexts | `METHOD M_LoadDefaultTexts` | Тексты по умолчанию (однократно при первом цикле) |

Карта аварий по умолчанию:
| ID | Авария | Источник |
|---|---|---|
| 0 | Таймаут состояния машины | FB_PackML.bError |
| 1 | Обрыв аварийной цепи (дверь/грибок) | FB_SafetyMonitor.bFault |
| 2 | Залипание кнопки пульта | FB_ButtonStuck.bError |
| 3..10 | Пневмоцилиндр 1..8: геркон не обнаружен | FB_PneumoCylinder[1..8].bError |
| 11..18 | Датчик 1..8: залипание / длительный засвет | FB_SensorStuck[1..8].bError |
| 19..47 | Резерв библиотеки | — |
| 48..63 | Резерв разработчика | прикладная программа |

Тексты по умолчанию (M_LoadDefaultTexts): 0='Таймаут состояния машины', 1='Обрыв аварийной цепи (дверь/грибок)', 2='Залипание кнопки пульта', 3..10='Пневмоцилиндр N: геркон не обнаружен', 11..18='Датчик N: залипание / длительный засвет'.

Зависимости: собирает bError/bFault от FB_PackML, FB_SafetyMonitor, FB_ButtonStuck, FB_PneumoCylinder[], FB_SensorStuck[]; bAck от команды Clear (FB_OperatorButtons).

---

### 2.9. FB_CycleTimeAnalyzer — FB — PackML: косвенно (bRunning = Execute)
Анализ длительности цикла: среднее/мин/макс, предупреждение о деградации (цикл > среднее x rTolerance) — ранний признак износа механики.

```iecst
VAR_INPUT
    bCycleDone  : BOOL;             // импульс "цикл завершён"
    bRunning    : BOOL;             // машина в Execute
    rTolerance  : REAL := 1.2;      // допуск: цикл > среднее x 1.2 = предупреждение
END_VAR
VAR_OUTPUT
    tLast, tAvg, tMin, tMax : TIME;
    nCycles     : DINT;
    bDegraded   : BOOL;             // цикл деградировал
END_VAR
VAR
    _tonCycle   : TON;
    _rDone      : R_TRIG;
    _liSum      : LREAL;
END_VAR
```
`_tonCycle(IN := bRunning, PT := T#24h);` — накопление статистики по фронту bCycleDone, перезапуск отсчёта.

---

### 2.10. FB_FirstFault — FB — PackML: нет
Регистратор первопричины: фиксирует первый фронт в массиве аварий (при цепочке аварий остальные — следствие).

```iecst
VAR_INPUT
    aFaults   : ARRAY[0..63] OF BOOL;
    bReset    : BOOL;
END_VAR
VAR_OUTPUT
    nFirst    : INT := -1;          // ID первопричины (-1 = не зафиксирована)
    bCaptured : BOOL;
END_VAR
```
В PRG_Machine: `fbFirstFlt(aFaults := aAlarmTrig, bReset := fbAlarms.bAnyActive = FALSE);`

---

### 2.11. FB_EventLogger — FB — PackML: косвенно (логирует смену состояний PackML)
Кольцевой журнал последних 64 событий (смена состояния, команды, аварии) с метками времени — разбор инцидентов без SCADA.

```iecst
VAR_INPUT
    dtNow : DT;                     // текущее время ПЛК (SYSGETTIME / часы реального времени)
END_VAR
VAR
    _aText : ARRAY[0..63] OF STRING(80);
    _aTime : ARRAY[0..63] OF DT;
    _nHead : INT;
    _nCnt  : INT;
END_VAR
```
| Элемент | Сигнатура | Назначение |
|---|---|---|
| M_Log | `METHOD M_Log` / `VAR_INPUT sText : STRING(80); END_VAR` | Добавить событие: `_nHead := (_nHead + 1) MOD 64;` |
| M_Get | `METHOD M_Get : STRING(80)` / `VAR_INPUT nBack : INT; END_VAR` | Чтение: nBack=0 — самое свежее; `nIdx := (_nHead - 1 - nBack + 64) MOD 64;` |
| P_Count | `PROPERTY P_Count : INT` (GET) | Количество событий в журнале |

---

### 2.12. FB_Heartbeat — FB — PackML: нет
Двусторонний контроль живости: свой меандр «ПЛК жив» наружу (bLifeBit + счётчик UINT) и контроль внешнего heartbeat (таймаут тишины -> bComError).

```iecst
VAR_INPUT
    bExternalHB : BOOL;             // heartbeat внешней системы
    bMonEnable  : BOOL := FALSE;    // включить контроль внешнего heartbeat
    tTimeout    : TIME := T#5s;
    tPulse      : TIME := T#500ms;
END_VAR
VAR_OUTPUT
    bLifeBit    : BOOL;             // наш меандр наружу
    nLifeCounter: UINT;             // счётчик (для протоколов, где нужен номер)
    bComError   : BOOL;             // внешняя система молчит > tTimeout
END_VAR
VAR
    _ton1, _ton2 : TON;
    _tonSilent   : TON;
    _bExtPrev    : BOOL;
END_VAR
```
Свой меандр на паре TON (`_ton1(IN := NOT _ton2.Q, PT := tPulse);`); любое переключение bExternalHB перезапускает таймер тишины; `bComError := _tonSilent.Q;`.

---

### 2.13. FB_ProductionStats — FB — PackML: косвенно (bRunning = Execute)
Производственная статистика: счётчики годных/брака, наработка в Execute, % брака — база для OEE на HMI.

```iecst
VAR_INPUT
    bGoodPulse   : BOOL;            // импульс: годное изделие
    bRejectPulse : BOOL;            // импульс: брак
    bRunning     : BOOL;            // Execute
    bReset       : BOOL;
END_VAR
VAR_OUTPUT
    nGood, nReject : DINT;
    tRunTime       : TIME;          // суммарная наработка
    rRejectRate    : REAL;          // % брака
END_VAR
VAR
    _rGood, _rRej : R_TRIG;
    _tonRun       : TON;
    _tAccum       : TIME;
END_VAR
```
Наработка: `_tonRun(IN := bRunning, PT := T#24h); tRunTime := _tAccum + _tonRun.ET;` — аккумулирование при паузах. `rRejectRate := DINT_TO_REAL(nReject) * 100.0 / DINT_TO_REAL(nGood + nReject);` при nGood+nReject > 0.

---

## 3. PROGRAM

### 3.1. PRG_Machine — PROGRAM — PackML: ДА (пример интеграции)
Скелет главной программы, связывающий все модули. Физические входы/выходы условные (%IX/%QX).

Локальные экземпляры:
```iecst
PROGRAM PRG_Machine
VAR
    // --- Ядро ---
    fbBlinker   : FB_Blinker;
    fbPackML    : FB_PackML;
    fbTower     : FB_TowerLight;
    fbButtons   : FB_OperatorButtons;
    fbBtnStuck  : FB_ButtonStuck;
    fbSafety    : FB_SafetyMonitor;
    fbAlarms    : FB_AlarmManager;
    fbCycle     : FB_CycleTimeAnalyzer;
    fbFirstFlt  : FB_FirstFault;
    fbLogger    : FB_EventLogger;
    // --- Периферия ---
    aCyl        : ARRAY[1..4] OF FB_PneumoCylinder;
    aSen        : ARRAY[1..4] OF FB_SensorStuck;
    aAlarmTrig  : ARRAY[0..63] OF BOOL;
    aBtnRaw     : ARRAY[1..16] OF BOOL;
    aBtnInv     : ARRAY[1..16] OF BOOL;
    aSafety     : ARRAY[1..32] OF BOOL;
    i           : INT;
    eStatePrev  : E_PackMLState;
END_VAR
```

Порядок вызовов (важно):
1. Безопасность первым: `fbSafety(aSignals := aSafety, nCount := 3, bMachineRunning := fbPackML.P_IsExecute OR fbPackML.M_IsActing(), bStartAttempt := fbButtons.bCmdPulse AND fbButtons.eCmd = E_PackMLCommand.Start, bReset := fbButtons.bCmdPulse AND fbButtons.eCmd = E_PackMLCommand.Clear);`
2. Кнопки: fbButtons(... eState := fbPackML.eState, bBlinkSlow := fbBlinker.bSlow, bBlinkFast := fbBlinker.bFast)
3. FB_ButtonStuck на нормализованных выходах fbButtons.bXxxPressed (aBtnInv := FALSE)
4. Машина состояний: `fbPackML();` затем `IF fbButtons.bCmdPulse THEN fbPackML.M_Command(fbButtons.eCmd); END_IF` и `IF fbSafety.bCmdAbort THEN fbPackML.M_Command(E_PackMLCommand.Abort); END_IF`
5. Прикладная логика acting-состояний: CASE fbPackML.eState — Resetting/Starting/Stopping/Aborting/Clearing/Completing -> `fbPackML.M_ActorDone();`
6. Цилиндры/датчики в циклах FOR 1..4; bReset := fbPackML.eState = E_PackMLState.Clearing; aSen[i].bEnable := fbPackML.P_IsExecute
7. Сбор аварий: aAlarmTrig[0] := fbPackML.bError; [1] := fbSafety.bFault; [2] := fbBtnStuck.bError; [2+i] := aCyl[i].bError (ID 3..6); [10+i] := aSen[i].bError (ID 11..14)
8. `fbAlarms(aTriggers := aAlarmTrig, bAck := fbButtons.bCmdPulse AND fbButtons.eCmd = E_PackMLCommand.Clear);`
9. `fbFirstFlt(aFaults := aAlarmTrig, bReset := fbAlarms.bAnyActive = FALSE);`
10. Индикация: fbBlinker(); fbTower(eState := fbPackML.eState, ..., bMuteBuzzer := fbAlarms.bAnyActive = FALSE); вывод на %QX0.0..%QX1.0
11. Журнал: `IF fbPackML.eState <> eStatePrev THEN fbLogger.M_Log(fbPackML.P_StateText); eStatePrev := fbPackML.eState; END_IF`

---

## 4. GVL / константы

- Глобальных списков переменных (GVL) в документе НЕТ.
- Единственная константа: `RESERVED_FROM : INT := 48` в `VAR CONSTANT` внутри FB_AlarmManager (граница резерва разработчика 48..63).

---

## 5. Элементы, связанные с PackML / ISA-TR88 (OMAC)

| Элемент | Тип | Связь с PackML |
|---|---|---|
| E_PackMLState | DUT (ENUM) | ДА — 17 состояний ISA-TR88 (acting 1..10, wait 11..17) |
| E_PackMLCommand | DUT (ENUM) | ДА — 9 команд + None (Reset/Start/Stop/Hold/Unhold/Suspend/Unsuspend/Abort/Clear) |
| FB_PackML | FB | ДА — ядро: машина состояний, таймаут acting-состояний, M_Command/M_ActorDone/M_IsActing, P_StateText/P_IsExecute/P_IsIdle/P_IsAborted |
| FB_TowerLight | FB | ДА — индикация жёстко привязана к eState (ARRAY[E_PackMLState] OF WORD), таблица по умолчанию — рекомендация по PackML |
| FB_OperatorButtons | FB | ДА — формирует команды eCmd по eState; длинный «Стоп» = Abort |
| FB_SafetyMonitor | FB | ДА — выдаёт команду Abort при обрыве аварийной цепи в работе; bMachineRunning := P_IsExecute OR M_IsActing() |
| FB_AlarmManager | FB | Косвенно — авария ID 0 = FB_PackML.bError; квитирование через команду Clear |
| FB_CycleTimeAnalyzer | FB | Косвенно — bRunning = состояние Execute |
| FB_ProductionStats | FB | Косвенно — bRunning = состояние Execute |
| FB_EventLogger | FB | Косвенно — логирует P_StateText при смене состояния |
| FB_SensorStuck | FB | Косвенно — в примере bEnable := P_IsExecute, bReset := состояние Clearing |
| FB_PneumoCylinder | FB | Косвенно — в примере bReset := состояние Clearing |
| PRG_Machine | PROGRAM | ДА — интеграция; Clearing = шина сброса всех диагностических модулей |

Отдельные замечания по PackML:
- Unit modes (Production/Manual/Maintenance) в документе НЕ реализованы — есть только состояния и команды.
- StateChanged: отдельного выхода нет; есть выход `eStatePrev : E_PackMLState` и внутренний импульс `_bEntered` (1 цикл при входе в состояние). В PRG_Machine смена состояния определяется сравнением `fbPackML.eState <> eStatePrev`.
- Abort — абсолютный приоритет: из любого состояния (кроме Aborted/Aborting) -> Aborting.
- Ошибки ядра: nErrorID: 1 = таймаут состояния, 2 = недопустимая команда.

---

## 6. Матрица зависимостей (кто кого использует)

| Блок | Использует (входы/типы) | Используется кем |
|---|---|---|
| FB_Blinker | TON (станд.) | FB_TowerLight, FB_OperatorButtons (bSlow/bFast) |
| FB_PackML | E_PackMLState, E_PackMLCommand, TON | FB_TowerLight, FB_OperatorButtons, FB_SafetyMonitor, FB_AlarmManager, FB_CycleTimeAnalyzer, FB_ProductionStats, FB_EventLogger, PRG_Machine |
| FB_TowerLight | FB_PackML.eState, FB_Blinker, E_PackMLState, E_LightMode | PRG_Machine (выходы на %QX) |
| FB_OperatorButtons | FB_PackML.eState, FB_Blinker, E_PanelMode, E_PackMLCommand, R_TRIG/F_TRIG/TON | FB_PackML (команды), FB_ButtonStuck (bXxxPressed), FB_SafetyMonitor (bStartAttempt), FB_AlarmManager (bAck по Clear) |
| FB_PneumoCylinder | E_CylSensors, TON | FB_AlarmManager (ID 3..10), PRG_Machine |
| FB_SensorStuck | TON, F_TRIG | FB_AlarmManager (ID 11..18), PRG_Machine |
| FB_ButtonStuck | FB_OperatorButtons.bXxxPressed (или сырые входы), TON | FB_AlarmManager (ID 2) |
| FB_SafetyMonitor | FB_PackML (P_IsExecute, M_IsActing), FB_OperatorButtons (команды Start/Clear), R_TRIG, TON | FB_PackML (bCmdAbort -> M_Command(Abort)), FB_AlarmManager (ID 1) |
| FB_AlarmManager | bError/bFault от всех диагностических FB | PRG_Machine (HMI, bMuteBuzzer, сброс FirstFault) |
| FB_CycleTimeAnalyzer | bRunning=Execute, R_TRIG, TON | PRG_Machine |
| FB_FirstFault | массив aAlarmTrig (тот же, что у FB_AlarmManager) | PRG_Machine |
| FB_EventLogger | DT (системное время), FB_PackML.P_StateText | PRG_Machine |
| FB_Heartbeat | TON | автономен; в PRG_Machine не инстанцирован |
| FB_ProductionStats | bRunning=Execute, R_TRIG, TON | автономен; в PRG_Machine не инстанцирован |

Архитектурный принцип: модули не знают друг о друге напрямую — связь выполняется в PRG_Machine через простые типы (BOOL, E_PackMLState, TIME). Централизованный сброс: состояние Clearing = шина сброса всех диагностических модулей.

---

## 7. Соглашения об именовании (раздел 11 документа)

- Префиксы: `bXxx` (BOOL), `eXxx` (enum), `tXxx` (TIME), `nXxx` (INT), `rXxx` (REAL), `aXxx` (массив), `sXxx` (STRING); внутренние переменные — `_xxx`; методы `M_Xxx`; свойства `P_Xxx`.
- Инкапсуляция: внутреннее состояние — в VAR и PRIVATE-методах; наружу только входы/выходы, методы, свойства.
- Импульсные сигналы: все команды/подтверждения — 1 цикл (bCmdPulse, bActionAck); потребитель обязан обработать в том же цикле.
- Стандартные элементы IEC: TON, R_TRIG, F_TRIG; функции LIMIT, MAX, SHR/SHL; преобразования TIME_TO_LREAL, LREAL_TO_TIME, INT_TO_LREAL, DINT_TO_LREAL, DINT_TO_REAL, WORD_TO_DWORD, DWORD_TO_WORD.

## 8. Идеи расширения (упомянуты, но НЕ реализованы в документе)

FB_ValveFeedback (контроль команда/отклик клапанов и пускателей — обобщение модуля 4), FB_AirConsumption (расход воздуха по импульсам расходомера), FB_TemperatureTrend (тренд температур с предупреждением), FB_DataExchange (упаковка диагностики в структуру для OPC UA / SCADA).
