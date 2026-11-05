# Платформы на базе CODESYS: обзор производителей

CODESYS — не только IDE: это рантайм (CODESYS Control), который лицензируют
500+ производителей. Ниже — карта основных платформ для ориентира при
переносе проектов (наш код на чистом IEC 61131-3/ST переносим между ними).

## Таблица платформ

| Производитель | Платформа | Особенности |
|---|---|---|
| **WAGO** | PFC100/PFC200 (CODESYS 3.5) | RT-Linux, Docker, firewall/VPN; 750-серия I/O (>500 модулей); полевые шины из коробки: EtherCAT Master, EtherNet/IP Scanner/Adapter, Modbus TCP; лицензируемые надстройки: BACnet, IEC 60870/61850, DNP3, Sparkplug, Multi-Cloud |
| **Phoenix Contact** | PLCnext (AXC F 2152/1152, RFC) | Гибрид: CODESYS (runtime отдельно, «CODESYS Control for PLCnext SL») + PLCnext Engineer; открытая ОС: C++, C#, Python, Docker параллельно с PLC |
| **Schneider Electric** | Modicon M241/M251/M262 (EcoStruxure Machine Expert) | IDE — форк CODESYS 3; особенности/грабли переноса проектов между вендор-форками |
| **Festo** | CPX-E-CEC / CPX-AP | CODESYS 3.5 + Festo PtP motion (CiA 402), VTUX-клапаны; см. festo-codesys-mcp в [mcp_servers_comparison](../03_AI_Prompts_and_MCP/mcp_servers_comparison.md) |
| **Bosch Rexroth** | IndraControl / ctrlX CORE (PLC app) | ctrlX: CODESYS-приложение в экосистеме apps; coUnit работает (xUnitFilePath под настройку) |
| **ifm** | CR/AL-контроллеры | Компактные CODESYS-контроллеры |
| **Pilz** | PSS 4000 | CODESYS Safety (сертифицированное безопасное программирование) |
| **Beckhoff** | TwinCAT 3 | Не CODESYS-рантайм, а родственная ветвь (общие корни IEC 61131-3); ST-совместимость высокая, библиотеки — нет; SPT/PackML-эталоны у нас как раз TwinCAT |
| **Raspberry Pi / Linux x86** | CODESYS Control for Raspberry Pi SL / Linux SL / Virtual Control SL | Обучение/софт-ПЛК; Pi — €55 (некоммерч.), Linux/Virtual Control — бесплатные рантаймы |

## Сравнение CODESYS vs PLCnext (по plcprogramming.io)

* CODESYS: ниже порог входа (2–4 мес.), ~70% adoption, 500+ вендоров железа.
* PLCnext: 4–8 мес. обучения, открытость (многоязычие + Docker), сильна в
  Industry 4.0/IoT-сценариях.
* Оба бесплатны на уровне инженерного ПО (платишь за рантайм/железо).

## Грабли переноса между платформами

1. Вендор-форки IDE (Machine Expert и т.п.) — версии библиотек отличаются.
2. TwinCAT ≠ CODESYS: нет 100% совместимости библиотек (OSCAT в TwinCAT
   требует правки ссылок).
3. Системные библиотеки (SysLib*) привязаны к рантайму.
4. Визуализация: WebVisu/TargetVisu — отдельные лицензии и настройки.
5. 32 vs 64 бита: часть библиотек (OSCAT) только 32-bit.

## TODO

* [ ] Детальные заметки по платформе заказчика по мере появления проектов.
* [ ] Матрица «фича → платформа → лицензия» для типовых проектов.
