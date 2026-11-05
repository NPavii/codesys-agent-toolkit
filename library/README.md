# Kimi_Lib — самописная библиотека CODESYS

Собственная библиотека решений для проектов CODESYS (IEC 61131-3, Structured Text) —
«цифровая копия лучших решений». Пополняется по мере работы: проверенные решения
переносятся сюда, документируются и становятся доступны всем агентам и проектам.

> **Важно:** файл библиотеки `Kimi_Lib.library` (как и любые другие файлы
> CODESYS-приложений — `.project`, `.library`, `.compiled-library`) в этот
> репозиторий **не включён**. Документ описывает архитектуру и может
> использоваться как ТЗ для собственной реализации. Рабочие правила ведения
> такой библиотеки — в [docs/04-kimi-lib.md](../docs/04-kimi-lib.md).

- **Источник истины** — один файл `.library` в вашей области (правится
  напрямую через MCP-инструменты `codesys-mcp` — см. [NPavii/codesys-mcp-server](https://github.com/NPavii/codesys-mcp-server))
- **Валидация**: компиляция `.library` напрямую через `check_all_pool_objects()`
  (операция `validate_library` моста, standalone, ~7 с, без проекта-зеркала).
- Статус референсной реализации: **0 ошибок, 0 предупреждений** (CODESYS V3.5 SP21 Patch 1; pool-check)
- Дата создания фундамента: 2026-09-17; переход на `.library`: 2026-09-18
- Рабочие правила агента, из которого выросла библиотека: [docs/01-workflow.md](../docs/01-workflow.md), [docs/04-kimi-lib.md](../docs/04-kimi-lib.md)
- Комментарии в коде — **на английском**; документация — на русском
- Агент **вправе сам пополнять библиотеку** типовыми решениями (критерии и чек-лист — в docs/04-kimi-lib.md)
- Агент **обязан обновлять README библиотеки** (история версий + состав) после каждого изменения
- **Удаление/переписывание блоков — только по явной команде владельца** и только
  указанного блока; самопроизвольные удаления запрещены

## Фундамент: PackML (OMAC) — контроль состояния оборудования

Фундамент — **не наш код, а установленная библиотека 3S** `OMAC_PackML_State_Machine`
v1.0.0.4 (`C:\ProgramData\CODESYS\Managed Libraries\...`), подключённая к Kimi_Lib
как зависимость. В коде используется напрямую через неймспейс `PACK_ML`:
`PACK_ML.State`, `PACK_ML.IUnitMode`, `PACK_ML.UnitMode`, `PACK_ML.UnitModeManager`.
Дублировать состояния/режимы в Kimi_Lib **не нужно** (ранее дублировали — удалено
в v0.4.0). Исходники оригинала поставляются с CODESYS — справочно.

Идея: **всё технологическое программирование пишется под состояние оборудования,
а набор состояний и разрешения конфигурируются в ФБ.** Агент/программист не пишет
«шпиндель вкл/выкл» в разных местах — он пишет код в ветках `CASE eState OF ...`.

### Состав (Kimi_Lib поверх PACK_ML)

| Объект | Тип | Назначение |
|---|---|---|
| `EquipmentCfg` | FB | **Конфигуратор оборудования v3** поверх `PACK_ML.UnitMode`. Две роли: (1) конфигурация — по фронту `xConfigure` (и при первом вызове) конфигурирует UnitMode один раз; (2) рантайм — фронты кнопок (`xStartBtn/xStopBtn/xResetBtn`, R_TRIG внутри) ведут переходы PackML, acting-состояния завершаются импульсом `xDone`. Публичные методы: `NextState()` (следующее состояние с фолбэками против `dwSupportedStates`: Holding→Held→UnHolding→Execute, Stopping→Stopped→Idle, Clearing→Stopped→Idle, нет Starting→Execute и т.д.), `StateEntered(eState)`, `GetUnitMode()` → `PACK_ML.IUnitMode`. Выходы: `eCurrentState`, `dwStateEntered`, `xCmdRejected`, `xLongStop` |

Правила переходов v3: Idle/Stopped+Пуск → Starting (нет Starting → Execute; блок `xErr`); Пуск в Execute → stop-путь (тумблер); Стоп короткий/долгий → Stopping (фолбэк на следующее поддерживаемое); Сброс → Aborted:Clearing, Stopped/Complete:Resetting.

Зависимости библиотеки: `OMAC PackML State Machine` (vendor, namespace `PACK_ML`) и системная `Standard` (TON, R_TRIG, F_TRIG). Тайминг: стандартные TON или виртуальные часы вызывающего (`tNow : TIME`, инкремент за скан) — без чтений системного времени в цикле.

### Как программировать под состояние (паттерн библиотеки)

```st
PROGRAM PLC_PRG
VAR
    fbDozer : Kimi_Lib.EquipmentCfg;  // конфигуратор дозатора
END_VAR

fbDozer(sName := 'Dozer',
        dwSupportedStates := PACK_ML.State.All,
        xStartBtn := xBtnStart, xStopBtn := xBtnStop, xResetBtn := xBtnReset,
        xErr := xAnyErr,
        xDone := xCycleDone);

CASE fbDozer.eCurrentState OF
    PACK_ML.State.Idle:
        // оборудование в ожидании
    PACK_ML.State.Execute:
        // основной цикл работы
    PACK_ML.State.Aborted:
        // аварийное состояние
END_CASE

// следующее состояние с учётом маски поддерживаемых:
eNext := fbDozer.NextState();

// односкановый импульс при входе в состояние:
IF fbDozer.StateEntered(PACK_ML.State.Execute) THEN
    // инициализация цикла
END_IF
```

Кнопки — уровни, фронты детектируются внутри FB (R_TRIG). Недопустимая команда не рвет цикл — взводится `xCmdRejected` на один цикл.
`xDone` сообщает, что «действующее» состояние (Starting, Execute, ...) завершено, — переход к следующему состоянию через резолвер с фолбэками.

### Проектирование под интерфейс

`PACK_ML.UnitModeManager` работает только через `PACK_ML.IUnitMode`. Экземпляр
`EquipmentCfg` можно отдать менеджеру: `fbManager.Register(fbEquip.GetUnitMode());` —
тогда переключение режимов `fbManager.SwitchUnitMode('ИмяРежима')` контролирует всю линию.

## Блоки MachineLib (перенос v0.3.0, референс — документация MachineLib, сторонний продукт)

Реализованы все модули, документированные в MachineLib. Тайминг (v0.5.0+): стандартные
TON для импульсов/задержек, виртуальные часы вызывающего `tNow : TIME` (инкремент за скан)
для измерения длительностей — без чтений системного времени в цикле задачи.
PackML-состояния и режимы **не дублируются** — берутся из vendor-библиотеки (`PACK_ML.*`).

| Объект | Тип | Назначение | Соответствие MachineLib |
|---|---|---|---|
| `EquipmentCfg` | FB | Конфигуратор поверх `PACK_ML.UnitMode` (см. фундамент) | `FB_PackML` — не дублировали, надстройка над vendor |
| `E_LightMode` | ENUM | Режим канала лампы: Off / On / BlinkSlow / BlinkFast | `E_LightMode` |
| `E_PanelMode` | ENUM | Раскладка кнопок пульта: StartStopToggle / StartStopSeparate | `E_PanelMode` |
| `E_CylSensors` | ENUM | Конфигурация датчиков пневмоцилиндра: StartOnly / StartEnd | `E_CylSensors` |
| `FB_TimerMs` | FB | Таймер задержки включения на внешнем тике (с v0.5.0 библиотека его не использует — оставлен как утилита) | инфраструктура |
| `FB_Blinker` | FB | Генератор мигания: медленный (1 Гц) и быстрый (4 Гц) каналы, TON | `FB_Blinker` |
| `FB_TowerLight` | FB | Светосигнальная колонна + зуммер по состоянию PackML; таблица по умолчанию (`M_LoadDefaults`), настройка через `M_SetStateConfig` | `FB_TowerLight` |
| `FB_OperatorButtons` | FB | Кнопки пульта → команды PackML; нормализация NO/NC, длинный Stop → Abort, режим одной кнопки Пуск/Стоп | `FB_OperatorButtons` |
| `FB_SafetyMonitor` | FB | Надзор цепи безопасности (NC-цепочки); запрос Abort при размыкании на ходу. НЕ замена аппаратному реле безопасности | `FB_SafetyMonitor` |
| ~~`FB_AlarmManager`~~ | — | **Удалён в v0.5.0** (по команде владельца — плохая затея): штатный путь аварий — Alarm Configuration CODESYS + `FB_FirstFault` + `FB_EventLogger` | — |
| `FB_PneumoCylinder` | FB | Контроль хода пневмоцилиндра с самообучением времени хода (скользящее среднее × запас) | `FB_PneumoCylinder` |
| `FB_SensorStuck` | FB | Детекция залипшего датчика: обучение нормальному времени ON, авария при превышении | `FB_SensorStuck` |
| `FB_ButtonStuck` | FB | Детекция залипших кнопок (до 16, с NC-инверсией) | `FB_ButtonStuck` |
| `FB_CycleTimeAnalyzer` | FB | Статистика времени цикла: last/avg/min/max + флаг деградации | `FB_CycleTimeAnalyzer` |
| `FB_FirstFault` | FB | Захват первой аварии: фиксирует индекс первой активной до сброса | `FB_FirstFault` |
| `FB_EventLogger` | FB | Кольцевой журнал событий (64 записи) с метками времени | `FB_EventLogger` |
| `FB_Heartbeat` | FB | Генератор heartbeat (бит жизни + счётчик) и монитор внешнего heartbeat | `FB_Heartbeat` |
| `FB_ProductionStats` | FB | Статистика производства: счётчики годных/брака, наработка, процент брака | `FB_ProductionStats` |

Roadmap (в MachineLib перечислены в разделе «Что ещё можно добавить позже» —
в документе только идеи, без спецификаций; не реализованы):
`FB_ValveFeedback`, `FB_AirConsumption`, `FB_TemperatureTrend`, `FB_DataExchange`.

## Как использовать этот дизайн в своём проекте

1. Реализуйте блоки по спецификациям ниже (или адаптируйте под свои
   обозначения) в своей библиотеке `.library`.
2. Валидация: `check_all_pool_objects()` через мост (операция
   `validate_library`) — критерий 0 ошибок, 0 предупреждений.
3. Подключение к проекту — через Library Manager (`lib_install` в
   репозиторий библиотек + `lib_add` в проект), без копирования объектов
   в проект; использование по namespace (см. `docs/04-kimi-lib.md`).

## История версий

| Версия | Дата | Изменения |
|---|---|---|
| 0.5.0 | 2026-09-23 | **EquipmentCfg v3**: конфигурация одним вызовом (`xConfigure`/первый вызов) + кнопки внутри FB (`xStartBtn/xStopBtn/xResetBtn`, R_TRIG) + публичный `NextState()` с фолбэк-резолвером против `dwSupportedStates` (нет Starting→Execute, Holding→Held→UnHolding→Execute, Stopping→Stopped→Idle и т.д.). **Удалён `FB_AlarmManager`** (по команде владельца; аварии — Alarm Configuration + `FB_FirstFault` + `FB_EventLogger`). **Тайминг без `udiNowMs`**: `FB_Blinker`/`FB_ButtonStuck`/`FB_SafetyMonitor`/`FB_OperatorButtons` — стандартные TON; `FB_CycleTimeAnalyzer`/`FB_SensorStuck`/`FB_PneumoCylinder`/`FB_Heartbeat`/`FB_ProductionStats` — виртуальные часы `tNow : TIME` (инкремент за скан); фронты — R_TRIG/F_TRIG. Зависимость от системной Standard (TON/R_TRIG). Валидация: 0 ошибок, 0 предупреждений |
| 0.4.0 | 2026-09-21 | **Миграция фундамента на vendor-библиотеку.** Удалены дубли PackML: `PackState` (был `State`), `IUnitMode`, `UnitMode`, `UnitModeManager`, `GVL_Constants` — теперь используется установленная 3S `OMAC PackML State Machine` 1.0.0.4 через namespace `PACK_ML` (подключена как зависимость Kimi_Lib). `EquipmentCfg` переписан как надстройка над `PACK_ML.UnitMode` (тот же API + разрешения смены режима `dwAllowedLeaving/EnteringIntoStates`, методы `StateEntered`/`GetUnitMode` → `PACK_ML.IUnitMode`). Перенацелены `FB_OperatorButtons` и `FB_TowerLight` (`PACK_ML.State` вместо `PackState`). По команде владельца («не копировать PACKML, использовать существующую библиотеку»). Валидация: 0 ошибок, 0 предупреждений |
| 0.3.1 | 2026-09-20 | Без изменений кода. Инфраструктура: проверочное зеркало-проект упразднено — `validate_library` компилирует `.library` напрямую (`check_all_pool_objects()`, standalone, ~7 с). Валидация: 0 ошибок, 0 предупреждений |
| 0.3.0 | 2026-09-19 | Перенос модулей MachineLib (референс — документация MachineLib, сторонний продукт): +3 DUT (`E_LightMode`, `E_PanelMode`, `E_CylSensors`) и +14 FB (`FB_TimerMs`, `FB_Blinker`, `FB_TowerLight`, `FB_OperatorButtons`, `FB_SafetyMonitor`, `FB_AlarmManager`, `FB_PneumoCylinder`, `FB_SensorStuck`, `FB_ButtonStuck`, `FB_CycleTimeAnalyzer`, `FB_FirstFault`, `FB_EventLogger`, `FB_Heartbeat`, `FB_ProductionStats`). `E_PackMLState`/`FB_PackML` осознанно не дублировались — используются `PackState`/`UnitMode`/`EquipmentCfg`. **Переименование `State` → `PackState`**: имя `State` перекрывается переменной `AlarmGlobals.STATE : INT` из системной библиотеки `#AlarmManager` (dummy для notification action «write variable»), что давало сотни ошибок компиляции в проекте с Alarm Configuration. Таймеры — собственный `FB_TimerMs` с инжектируемым тиком `udiNowMs` (библиотека самодостаточна, без Standard). Валидация: 0 ошибок |
| 0.2.0 | 2026-09-18 | Перенос источника истины в `.library`. PackML-фундамент (State, IUnitMode, UnitMode, UnitModeManager) + EquipmentCfg перенесены и проходят валидацию: 0 ошибок, 0 предупреждений |
| 0.1.0 | 2026-09-17 | Фундамент: PackML (State, IUnitMode, UnitMode, UnitModeManager) + EquipmentCfg. Компиляция 0 ошибок |

## Эталонные материалы

- Спецификация PackML (OMAC, ISA TR88.00.02) — официальный документ OMAC.
- Исходники оригинальной библиотеки 3S `OMAC_PackML_State_Machine` и официальный
  пример `PackML_Example.project` поставляются с CODESYS (см. установленные
  примеры и managed-библиотеки) — в репозиторий не включены.
