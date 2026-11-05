# Стратегии тестирования в CODESYS

## Юнит-тесты: co♻e (coUnit)

Дом проекта: `forge.codesys.com/lib/counit/` (Forge — официальная
community-площадка CODESYS; там тикеты, туториал, API-reference).
GitHub-зеркало: `Aliazzzz/coUnit`. Лицензия MIT. Форк TcUnit
(Jakob Sagatowski). Пакет: библиотека `coUnit.library` + примеры проектов
(Simple Example, Timed Test, Verifier).

### Паттерн TDD (пример из туториала)

```st
// 1. Тест-сьют наследует FB_TestSuite
FUNCTION_BLOCK FB_Sum_Test EXTENDS CoUnit.FB_TestSuite
// 2. Каждый тест — метод
METHOD TwoPlusTwoEqualsFour
VAR
    Sum : FB_Sum;
    Result : UINT;
END_VAR
TEST('TwoPlusTwoEqualsFour');
Sum(one := 2, two := 2, result => Result);
AssertEquals(Expected := UINT#4, Actual := Result,
             Message := 'The calculation is not correct');
TEST_FINISHED();   // разрешает тесты в несколько PLC-циклов

// 3. Тело сьюта вызывает методы-тесты
// 4. PRG_TEST (только для тестов, НЕ на прод-ПЛК!)
PROGRAM PRG_TEST
VAR fbSum_Test : FB_Sum_Test; END_VAR
CoUnit.RUN();
```

Результаты — в Device Log (логгер co♻e) и/или xUnit-файл (параметр
библиотеки `xUnitFilePath`; на ctrlX: `/var/snap/rexroth-solutions/common/
solutions/activeConfiguration/coUnit_xunit_testresults.xml`).

### CI/CD

* CODESYS CLI: `--runscript` исполняет python-скрипт (запуск проекта,
  чтение результатов); готовые скрипты пайплайна — тикет #64 на Forge.
* Интеграции: Jenkins, Azure DevOps, GitLab; xUnit-отчёты нативно
  подхватываются CI.
* CForge Drone CI/CD backend — бета-интеграция «из коробки».

## Уровни тестирования (по аналогии с CODESYS Test Manager)

| Уровень | Что проверяет | Инструмент |
|---|---|---|
| Unit | Отдельный FB/FUNCTION | co♻e |
| Integration | Взаимодействие модулей (интерфейсы PackML-модулей) | co♻e + симуляция |
| System | Приложение целиком на симуляторе | SoftPLC + скрипты MCP/моста |
| Virtual commissioning | Логика против цифрового двойника | CODESYS Simulation Interface (PDE) / внешние симуляторы через Modbus TCP |

## Что даёт нам мост/MCP (см. docs/02-bridge.md)

* Автотесты «на лету»: `build` после каждой правки (критерий 0/0),
  `eval` для программных проверок объектов.
* Прямой онлайн-цикл против SoftPLC: login → read/write → logout
  (`codesys_online_*`) — приёмочные тесты без железа.
* Идея на будущее: regression-pack для Kimi_Lib — набор FB-тестов на co♻e
  + запуск через демон в `validate_library`-пайплайне.

## Чек-лист тестируемости FB (для проектирования)

1. FB не читает глобалов напрямую — зависимости через VAR_IN_OUT/интерфейсы.
2. Нет скрытых таймеров «на глобальном времени» — входы через TON-экземпляры.
3. Детерминированный сброс состояния (M_Reset / FB_Reinit).
4. Граничные значения и NaN/переполнения — явная обработка.
