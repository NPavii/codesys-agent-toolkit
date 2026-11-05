# Паттерны ООП в CODESYS (IEC 61131-3)

Источники: `Library/_ref/Applied-Design-Patterns-in-CODESYS-V3/` (проекты
Aliazzzz; первоисточники — S. Henneken, TwinCAT-блог; A. R. Narvaez Contreras,
CODESYS-форум). Ниже — канонические реализации на ST, согласованные с
`Rules/07-standards.md` (ООП: интерфейсы, наследование, инъекция зависимостей).

> Правило из репозитория-источника: «паттерны облегчают жизнь, но лучшее
> решение — простейшее, даже процедурное». Паттерн — инструмент, не цель.

## 1. Observer (Наблюдатель) — самый востребованный

Субъект ведёт список наблюдателей и оповещает их при изменении состояния.
В CODESYS: через `INTERFACE` + массив интерфейсных ссылок.

```st
INTERFACE IObserver
METHOD Update : BOOL
VAR_INPUT
    iValue : INT;
END_VAR
END_INTERFACE

INTERFACE ISubject
METHOD Attach : BOOL  VAR_INPUT o : IObserver; END_VAR
METHOD Detach : BOOL  VAR_INPUT o : IObserver; END_VAR
METHOD Notify
END_INTERFACE

FUNCTION_BLOCK ConcreteSubject IMPLEMENTS ISubject
VAR
    aObs    : ARRAY[1..10] OF IObserver;
    iCount  : INT;
    iState  : INT;
END_VAR

METHOD Notify
VAR i : INT;
END_VAR
FOR i := 1 TO iCount DO
    IF aObs[i] <> 0 THEN aObs[i].Update(iState); END_IF
END_FOR

METHOD Attach : BOOL
VAR_INPUT o : IObserver; END_VAR
IF iCount < 10 THEN iCount := iCount + 1; aObs[iCount] := o; Attach := TRUE; END_IF
```

Применение у нас: события/аварии PackML-модулей, подписка HMI на статус.

## 2. Command (Команда)

Инкапсуляция запроса как объекта: интерфейс `ICommand` с методом `Execute`,
конкретные команды оборачивают получателя (receiver). Invoker хранит очередь
команд — легко добавить undo/логирование/макросы.

```st
INTERFACE ICommand
METHOD Execute : BOOL
END_INTERFACE

FUNCTION_BLOCK FB_StartCommand IMPLEMENTS ICommand
VAR
    fbMachine : REFERENCE TO FB_PackMLUnit;  // receiver
END_VAR
METHOD Execute : BOOL
Execute := fbMachine.M_Start();
```

Применение: очередь команд оператора/HMI, кнопки визуализации, макросы режимов.

## 3. Abstract Factory (Абстрактная фабрика)

Создание семейств объектов без указания конкретного класса: интерфейс
`IFactory` с методом `Create` : `IProduct`; конкретные фабрики возвращают
нужную реализацию. Клиент зависит только от интерфейсов.

Применение: создание устройств одного типа (приводы разных вендоров,
датчики) по конфигурации `EquipmentCfg` — см. `Rules/04-kimi-lib.md`.

## 4. Builder (Строитель)

Отделение конструирования сложного объекта от его представления: Director
вызывает шаги `IBuilder` (Init/AddPart/Build). В PLC удобен для пошаговой
сборки конфигурации модуля (параметры, подмодули, компоненты) из рецепта.

## 5. Decorator (Декоратор)

Добавление поведения объекту обёрткой, реализующей тот же интерфейс:
декоратор держит ссылку на `IComponent` и делегирует + добавляет своё.
Применение: надстройки над базовым FB (логирование, тайм-ауты, счётчики
циклов) без изменения базового кода.

## 6. Proxy (Заместитель)

Объект-заместитель с тем же интерфейсом: ленивая инициализация, проверка
предусловий, кэш, доступ к удалённому/дорогому ресурсу.
Применение: прокси к оси/драйверу (проверка готовности перед вызовом),
прокси к OPC UA-тегам.

## 7. Singleton (Одиночка) — использовать с осторожностью

Ограничение класса одним экземпляром. В IEC 61131-3 честный статический
экземпляр FB недоступен, поэтому канонически: один экземпляр в `VAR_GLOBAL`
+ FB_Init-защита от повторной инициализации состояния. Автор источника
сам называет Singleton антипаттерном (глобальное состояние). В наших
проектах вместо Singleton — GVL с явными экземплярами (`Rules/07`).

## Связь с PackML/SPT

SPT Framework (`Library/_ref/PackML/SPT-Libraries/`) — практическое
применение этих же идей: `FB_PackML_BaseModule` (наследование/шаблонный
метод Initialize/CyclicLogic), компоненты (композиция, инъекция через
интерфейсы), события (Observer через EventLogger).

## TODO

* [ ] Извлечь точный код проектов через мост (`dump_tree`) и сверить
      детали реализаций — когда MCP/демон освободится.
* [ ] Добавить диаграммы (PlantUML) для каждого паттерна.
