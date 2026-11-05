# Стандартные и community-библиотеки

## Встроенные в CODESYS (поставляются с IDE/рантаймом)

| Библиотека | Назначение | Примечание |
|---|---|---|
| Standard | IEC-типы, TON/TOF/TP/R_TRIG/F_TRIG, строки,_TRIG-функции | Базовая, всегда подключена |
| Util (IEC 61131-3) | Доп. типы (BCD, периферия), детекторы фронтов, генераторы | Часть системного набора |
| SysLib* (SysSocket, SysFile, SysMem…) | API рантайма: сокеты, файлы, память, время | C-API-обёртки; нужны для собственных коммуникаций |
| CmModbus / Modbus FBs | Modbus TCP/RTU master/slave | Канонический стек от CODESYS |
| OPC UA (Client/Server) | OPC UA из коробки, интеграция с Symbol Configuration | Стандарт de-facto для IIoT |
| SM3_Basic / SM3_CNC (SoftMotion) | PLCopen Motion: оси, камы, CNC | Лицензируется отдельно |
| IoT/Connectivity-библиотеки | MQTT/REST через CODESYS IoT-коннекторы | Проверять наличие под конкретный рантайм |

## OSCAT (Open Source Community for Automation Technology)

* Репозиторий-архив: `github.com/eclipse-oscat/oscat-libs-archive` (read-only,
  исторические релизы). Документация: `oscat.readthedocs.io`.
* Порты под CODESYS V3 в CODESYS Store: **OSCAT BASIC** (арт. 604300, €0),
  **OSCAT BUILDING** (604302, €0). Требования: CODESYS ≥ 3.5.5.0,
  **только 32-битные платформы** (64-bit не поддерживается — важно!).
* Состав: BASIC (математика, строки, дата/время, регулирование, сигналы),
  BUILDING (HVAC, жалюзи, физика помещений), NETWORK (Modbus, FTP, e-mail,
  DNS, крипто RC4/MD5/SHA1, JSON-INI).
* **Безопасность**: CISA ICSA-24-326-02 — out-of-bounds read в OSCAT Basic
  (CVE-2024-6876), исправлено в BASIC ≥ 3.3.4.0/3.35. Использовать только
  свежую версию и валидировать входы строковых/буферных функций
  (`DELETE`, `INSERT`, `MID`).
* Грабли установки (проверено в полях): V2 `.lib` не открывается в V3;
  конфликты имён со Standard — решать через namespace/qualified_only;
  NETWORK под V3 официально не портирована (V2-версия через CAA).

## Тестирование

* **coUnit (co♻e)** — фреймворк юнит-тестов для CODESYS, форк TcUnit
  (Jakob Sagatowski) с разрешения. MIT. Дом: `forge.codesys.com/lib/counit/`
  (там же тикеты, tutorial, CI-интеграция Jenkins/Azure DevOps через
  `--runscript`; готовые python-скрипты пайплайна — тикет #64).
  GitHub-зеркало: `Aliazzzz/coUnit`. xUnit-отчёты, TDD-стиль:
  `FB_Xxx_Test EXTENDS CoUnit.FB_TestSuite` → `TEST('...')` → asserts →
  `TEST_FINISHED()` → `CoUnit.RUN()` в отдельном PRG_TEST.
  Параметр `xUnitFilePath` — путь экспорта результатов (на ctrlX:
  `/var/snap/rexroth-solutions/common/...`). Подробности и примеры:
  [testing_strategies.md](../05_Best_Practices/testing_strategies.md).
* Альтернативы (TwinCAT/кросс): TcUnit, UniTest (платформонезависимая).

## Community-библиотеки и утилиты (веб-обход 2026-09-21)

| Проект | Что это | Ценность |
|---|---|---|
| `WengerAG/structured-text-utilities` | Утилиты: массивы, числа, строки, дата/время | Чистый ST, можно брать идеи в Kimi_Lib |
| CiA402 motion layer (pure ST, CoDeSys 3.5 + TwinCAT) | Оси без SoftMotion/TF5000: homing, profile position/velocity, jog, CSP jerk-limited | Продакшн на CX8190; эталон CiA 402 на ST |
| `damischa1/iec-st-tools` (Go) | Конвертеры: `.st` ↔ CODESYS 2.3 `.EXP` ↔ 3.5 `.export` ↔ PLCopen XML TC6 | Для CI/CD и миграций |
| `Autonomy-Logic/STruCpp` | Компилятор ST → C++17 (IEC 61131-3 Ed.3, OOP, REPL, тесты); импорт `.lib`/`.library` | CI/CD: unit-тесты ST без ПЛК |
| PLCopen XML TC6 | Стандарт обмена POU между IDE | Основа интеграций (см. festo-codesys-mcp) |

## Критерии оценки сторонней библиотеки

1. Версия CODESYS в манифесте ≥ нашей (3.5.21.x) и не только 32-bit.
2. Лицензия (OSCAT/MIT — ок; «freeware без исходников» — риск).
3. Активность: коммиты/тикеты за последние 2 года.
4. Известные CVE (CISA ICS advisories) и грабли (см. `docs/06-pitfalls.md`).
5. Конфликты пространств имён со Standard/Util/Kimi_Lib.
