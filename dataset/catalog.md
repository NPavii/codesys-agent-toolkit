# Каталог датасета (Tier 0)

> Ищи по тегам/словам через grep: `grep -i "alarm" Library/_dataset/records/*.jsonl`
> Правила: см. [README.md](../README.md). Свежие записи — сверху раздела.

## PackML_Example.project — разбор на винтики (2026-09-21)

Официальный пример 3S к OMAC_PackML_State_Machine: 2 устройства (UnitModeManager с 3 режимами + AxisControl с SoftMotion). Полный дамп: `_ref/packml_example_dump.json`.

| ID | Что | Качество | Код |
|---|---|---|---|
| 2026-09-013 | Маски dwAllowsLeaving/EnteringIntoStates (смена режима) — НЕТ в Kimi_Lib, фича-кандидат | reference | code/2026-09-013_mode_change_masks.st |
| 2026-09-014 | One-shot init FB через xInit-флаг (без FB_Init, обходит падение SP21) | reference | code/2026-09-014_one_shot_init.st |
| 2026-09-015 | FB отдаёт свой интерфейс наружу (VAR_OUTPUT ItfUnitMode := UM) | reference | code/2026-09-015_iface_output_and_manager.st |
| 2026-09-016 | UnitModeManager: Register/ActiveUnitMode/SwitchUnitMode + откат UI при отказе | reference | code/2026-09-015_iface_output_and_manager.st |
| 2026-09-017 | Motion-FB (MC_*) под состояниями PackML: Wait сбрасывают Execute, ActingStateCompleted по Done, вызовы вне CASE | reference | code/2026-09-016_motion_under_states.st |
| 2026-09-018 | Визу-мост команд: BOOL-флаги → методы интерфейса | reference | code/2026-09-017_visu_bridge_simulate.st |
| 2026-09-019 | SimulateActingStateComplete: автодемо через NextState + TON (метод с доступом к VAR родителя) | reference | code/2026-09-017_visu_bridge_simulate.st |
| 2026-09-020 | Конфигурация режимов вычитанием масок: State.All - X - Y | reference | _ref/PackML_Example.project |

## SmartKeyV2 / TowerLightV2 / DoorGuard — ANK601 (2026-10, обкатано онлайн)

| ID | Что | Качество | Код |
|---|---|---|---|
| 2026-10-003 | SmartKeyV2: кнопка (глубина по отпусканию, LED, бизер+блокировка, дребезг, xLock/xAlarm) | verified | ANK601/ank601_3 |
| 2026-10-004 | TowerLightV2: светофор PackML (итог: одноцветный план R/O/G/B + оверлей дверей ЗАМЕЩАЕТ цвет + xMute) — см. 2026-10-009 | verified | ANK601/ank601_3 |
| 2026-10-005 | FB_DoorGuard + E_DoorPolicy: двери с градацией строгости 0..4 | verified | ANK601/ank601_3 |
| 2026-10-006 | F_PackML_Suspend/Pause: пауза одним вызовом (Suspend=внешние, Hold=оператор) | verified | ANK601/ank601_3 |
| 2026-10-007 | Грабля: методам запрещён VAR_IN_OUT родителя; FB в VAR_INPUT метода = копия | verified | — |
| 2026-10-008 | Hold vs Suspend: семантика пауз + финальная карта кнопок ANK601 (Start long=Completing, Action long+xAlarm в Stopped→xErrReset) | verified | ANK601/ank601_3 |
| 2026-10-009 | Односекционный светофор: одноцветный план + взаимоисключение + оверлей-дверей + Mute (паттерн) | verified | ANK601/ank601_3 |
| 2026-10-010 | FB_MD800: Innovance MD800 по EtherCAT — PDO-образ (команды 0..7, задание 0.01Hz), статус-биты→String, fault→String, speed-watchdog, главный модуль (bus/temp) | verified | ANK601/ank601_3 |
| 2026-10-011 | Паттерн патча ESI EtherCAT-устройства: DataType/Object в словарь + Entry в RxPdo/TxPdo (MD800: +0x2000 разгоны, +Fault code в 16#1A01) | verified | ESI XML |

## WebVisu-панель — ANK101 (2026-10-30, 0/0 build)

| ID | Что | Качество | Код |
|---|---|---|---|
| 2026-10-012 | WebVisu-панель без GUI: native_export → XML → native_import; карта Id-полей элемента, 1920×1080 (visu + клиент), замещение объектов (delete+rename), ремонт LM (placeholder Standard), генератор раскладки | verified | ANK101/_gen_panel.py + WebVisu_Demo_Panel.md |

## Прочие источники _ref

| ID | Что | Качество | Код |
|---|---|---|---|
| 2026-09-026 | EquipmentCfg v3: конфиг один раз + кнопки в FB + NextState с фолбэк-резолвером | verified | Kimi_Lib |
| 2026-09-027 | Конвенция тайминга: TON для импульсов, tNow-инкремент для длительностей, R_TRIG/F_TRIG | verified | Kimi_Lib |
| 2026-09-028 | FB_AlarmManager удалён; аварии = Alarm Configuration + FirstFault + EventLogger | verified | — |
| 2026-09-022 | GoF в ST: Singleton/Observer/Command/Decorator/Proxy (VAR_STAT, enable_dynamic_creation, массивы интерфейсов) | reference | code/2026-09-022_gof_patterns_st.st |
| 2026-09-023 | VAR_STAT — статика уровня типа FB (основа Singleton) | reference | code/2026-09-022_gof_patterns_st.st |
| 2026-09-024 | Observer: ARRAY OF I_Interface + register/notify с null-проверками | reference | code/2026-09-022_gof_patterns_st.st |
| 2026-09-021 | Инвентаризация _ref: design-patterns (8 GoF в ST), J1939, SoftMotion, Visu-доки, MQTT C-extern, OD Samples (MX308) | reference | — |

## PackML / state-machine (2026-09)

| ID | Что | Качество | Код |
|---|---|---|---|
| 2026-09-001 | Enum State: 17 состояний, битовая маска DWORD | verified | code/2026-09-001_state_enum.st |
| 2026-09-002 | Интерфейс IUnitMode (9 команд + свойства) | verified | Kimi_Lib |
| 2026-09-003 | Паттерн команды-метода (CASE + SupportedStates) | verified | code/2026-09-003_command_method_pattern.st |
| 2026-09-004 | ActingStateCompleted (acting→wait, Execute→Completing) | verified | code/2026-09-004_acting_completed_pattern.st |
| 2026-09-005 | FB UnitMode | verified | Kimi_Lib |
| 2026-09-006 | FB UnitModeManager (смена режимов) | verified | Kimi_Lib |
| 2026-09-009 | Матрица переходов + минимум PackTags (TR88.00.02) | verified | _ref/PackML/README.md |
| 2026-09-010 | Архитектура SPT (Initialize/CyclicLogic) | reference | _ref/PackML/SPT-Libraries/docs |
| 2026-09-011 | Правила: Stop/Abort/смена режима | verified | ISA-TR88 PDF |

## Kimi_Lib / прочее verified

| ID | Что | Качество | Код |
|---|---|---|---|
| 2026-09-007 | EquipmentCfg (конфигуратор оборудования) | verified | Kimi_Lib |
| 2026-09-008 | GVL_Constants | verified | Kimi_Lib |

## Вердикты / грабли

| ID | Что | Качество |
|---|---|---|
| 2026-09-012 | FieldFox MQTT-lib — НЕ пригодна (V2/WAGO, пустой код) | verified |
| 2026-09-013 | Мост: build падает «Некорректный дескриптор проекта» — сбой тёплой сессии; повторить/перезапустить демон | reference |
