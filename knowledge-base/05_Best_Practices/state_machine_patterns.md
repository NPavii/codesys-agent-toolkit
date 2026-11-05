# Паттерны конечных автоматов: PackML (ISA TR88.00.02)

> Полный разбор стандарта, 11 эталонных репозиториев и выводы для Kimi_Lib:
> [Library/_ref/PackML/README.md](../../Library/_ref/PackML/README.md) — там
> таблицы состояний/команд/переходов, PackTags и архитектура SPT.
> Здесь — сжатая рабочая выжимка для проектирования.

## Модель в трёх строках

17 состояний (битовая маска DWORD), 32 режима (Production/Maintenance/Manual
+ 28 кастомных), 9 команд (Reset, Start, Stop, Hold, Unhold, Suspend,
Unsuspend, Abort, Clear) + внутренняя StateComplete.

* **Wait-состояния** (Stopped, Idle, Held, Suspended, Complete, Aborted):
  выход только по команде.
* **Acting-состояния** (Starting, Stopping, Aborting, Holding, …, Execute):
  вход по команде/StateComplete, выход по StateComplete от логики.
* **Stop** — отовсюду кроме Abort-ветки (оператор); **Abort** — отовсюду
  (авария, выдаёт код). Смена режима — только из Wait-состояний, разрешённых
  обоими режимами.

## Эталонный паттерн реализации (OMAC CODESYS → Kimi_Lib)

```st
// Команда-метод: CASE по текущему состоянию + проверка поддержки состояния
METHOD Start : BOOL
CASE eState OF
State.Idle:
    IF (State.Starting AND SupportedStates) = 0 THEN
        Start := FALSE; RETURN;
    END_IF
    eState := State.Starting;
    Start := TRUE;
END_CASE

// Завершение acting-состояния: переход к парному Wait
METHOD ActingStateCompleted : BOOL
CASE eState OF
State.Holding, State.UnHolding, State.Starting, State.Completing,
State.Resetting, State.UnSuspending, State.Suspending, State.Aborting,
State.Stopping, State.Clearing:
    eState := NextState(eState);       // Acting → Wait
State.Execute:
    eState := State.Completing;        // цикл отработан
END_CASE
```

## Чего не хватает до «полного PackML» (дорожная карта Kimi_Lib)

1. Таблица валидных переходов «команда × состояние» (строже маски
   SupportedStates).
2. Структуры PackTags: `Command/Status/Admin` по TR88.00.02-2022
   (минимум ~14 тегов — см. `Library/_ref/PackML/README.md`, раздел 3).
3. Таймеры: StateTimeCurrent, ModeTimeCurrent, CumulativeTimes.
4. StopReason + ProductData (Processed/Defective) — задел под OEE.
5. Протокол команд через ChangeRequest (письмо → Request → применение → сброс).

## Архитектурный паттерн SPT (Beckhoff) — рекомендуемый каркас

```
Machine Module (PackML-автомат)      ← точка связи с линией
  └─ Equipment Modules / Submodules  ← каждый со СВОИМ автоматом
       └─ Components (axis, valve…)  ← БЕЗ автомата, самодостаточные FB,
                                        свои аварии, переиспользуемые
```

* `Initialize()` — многоскановый, до TRUE; `CyclicLogic()` — всегда
  циклически, первым делом завершает инициализацию.
* Код состояния — в переопределяемых методах (M_Starting, M_Execute…);
  «happy path» отделён от аварий/HMI/восстановления.
* Компоненты разрабатываются и тестируются вне фреймворка.

## TODO

* [ ] Пороговый CASE vs таблица переходов: бенчмарк читаемости в CODESYS.
* [ ] Дополнить: иерархия автоматов (sub-unit interlocks, Suspended-цепочка).
