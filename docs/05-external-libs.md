# Правило 05. Сторонние библиотеки: что использовать и как подключать

Порядок поиска готового решения перед написанием своего кода:
**своя библиотека решений → идеи MachineLib (docs/08-machinelib.md) → OSCAT → Standard/Util →
прочие (SM3, IoT) → своё решение** (с занесением в свою библиотеку, если типовое).

## Подключение

- Компилированные системные библиотеки ставятся через Library Manager в GUI
  или уже присутствуют в системном репозитории
  (`C:\ProgramData\CODESYS\Managed Libraries`).
- Свои/внешние `.library` — через мост: `lib_install` (в репозиторий) →
  `lib_add` (в проект). См. docs/02-bridge.md.
- Правила использования чужих библиотек — ниже (карта и правила из Rulebook).

## 8. Библиотеки: что есть и почему их нужно использовать

**Главное правило: не изобретайте то, что уже проверено.** Стандартные библиотеки оттестированы на десятках платформ; ваш самописный TON — нет.

### 8.1. Карта библиотек

| Библиотека | Что даёт | Когда подключать |
|---|---|---|
| **Standard** (Standard.library) | TON/TOF/TP, R_TRIG/F_TRIG, CTU/CTD, базовые функции IEC | Всегда (подключена по умолчанию) |
| **Util** | PID/регуляторы, фильтры (PT1, Hysteresis), Ramp, SignalGenerator, BCD/конвертеры, BitCounter | Любая аналоговая обработка, регулирование |
| **IoStandard / IoDrv***** | Работа с I/O-драйверами, диагностика модулей | Чтение состояния модулей I/O, диагностика шины |
| **SysFile / SysDir / SysTime / SysCom** | Файлы, директории, системное время, COM-порты на контроллере | Логи в файл, CSV-отчёты, RTC |
| **SysSem / SysTask** | Семафоры, синхронизация между задачами | Разделённые данные между задачами разных приоритетов |
| **OSCAT BASIC** | 500+ функций и FB: математика, строки, таймеры, PID, технологические блоки. Открытый код, независимость от вендора | Почти всегда, когда Standard/Util не хватает (Motion Control Tips: 2019-08-26([motioncontroltips.com](https://www.motioncontroltips.com/what-are-oscat-files-how-do-they-relate-to-codesys/))) |
| **OSCAT BUILDING / NETWORK** | Климат/здания; сеть и файлы | По профилю проекта |
| **SM3_Basic / SM3_CNC / PLCopen MC_*** | SoftMotion: оси, электронные кулачки, CNC | Любое движение |
| **IIoT: MQTT / JSON / OPC UA PubSub** | Интеграция с MES/облаком | Сбор данных, удалённый мониторинг (CODESYS Store: Janz Tec MQTT, OPC UA PubSub([store.codesys.com](https://store.codesys.com/en/catalogsearch/result/index/?p=2&q=codesys+function))) |
| **CAA-*** (CAA Memory, CAA File…)** | Проверенные низкоуровневые сервисы от CAA Technical Workgroup | Когда Sys*-библиотек мало |

### 8.2. Правила использования чужих библиотек

**[HIGH]** **L-1. Версии фиксируются.** В проекте — Library Manager с явными версиями (не «новейшая»). Обновление библиотеки = отдельное изменение с регрессионным тестом.

**[HIGH]** **L-2. Обращения через namespace.** `OSCAT_BASIC.TON_DELAY`, а не голое имя — иначе коллизии со Standard (классический конфликт «TON is implemented more than once») (Industrial Monitor Direct, установка OSCAT: 2026-07-12([industrialmonitordirect.com](https://industrialmonitordirect.com/zh-hans/blogs/knowledgebase/installing-oscat-basic-library-in-indraworks-v13-codesys-v3))).

**[MED]** **L-3. Проверка уязвимостей.** Пример: OSCAT BASIC до 3.3.4.0 имел CVE по out-of-bounds read (CISA ICSA-24-326-02) — перед использованием сверяйте версию и обновляйтесь (Industrial Monitor Direct: 2026-07-12, ссылка выше).

**[MED]** **L-4. Не выдумывать API библиотеки.** Агент обязан сверять имена и сигнатуры блоков с реально установленной версией в Library Manager, а не с памятью (см. гайдлайн codesys-mcp: «Confirm library functions in the CODESYS Library Manager» (CODESYS Help, Programming in ST([helpme-codesys.com](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_programming_in_st.html)))).

---

## 9. Пользовательские библиотеки (.library)

MachineLib и любой повторно используемый код оформляются как **библиотечный проект** (File → Save as → CODESYS Library / compiled library). Официальные требования к разработке библиотек (CODESYS Help, Guidelines for Creating Libraries([helpme-codesys.com](https://content.helpme-codesys.com/en/CODESYS%20Development%20System/_cds_guidelines_for_creating_libraries.html))):

**[HIGH]** **UL-1. Обязательный минимум:** осмысленное имя библиотеки; **уникальный зарегистрированный namespace**; заполненная информация о проекте (Company/Title/Version); корректные ссылки на другие библиотеки; продуманные внешние/внутренние интерфейсы; дружелюбная обработка ошибок; выбранный способ защиты при поставке.

**[HIGH]** **UL-2. Совместимость интерфейса при новой версии.** Семантическое версионирование: добавление входа со значением по умолчанию — minor; удаление/переименование — major. Удалять входы из опубликованного FB нельзя никогда.

**[MED]** **UL-3. Поставка без исходников — compiled library.** Скомпилированная библиотека не открывается в редакторе; шифрование с паролем запрашивает пароль при каждом использовании — почти никогда не нужно (CODESYS Forge, know-how-protect thread: 2015-03-10([forge.codesys.com](https://forge.codesys.com/forge/talk/CODESYS-V2/thread/f43680fc0c/))).

**[MED]** **UL-4. Документация внутри библиотеки.** Комментарий-заголовок каждого FB: назначение, входы/выходы, пример вызова, история версий. Внешняя документация (как MachineLib_Documentation.html) — часть релиза библиотеки.

**[MED]** **UL-5. Библиотека не знает о проекте.** Никаких ссылок на GVL конкретного станка. Связь с железом — через параметры и REFERENCE TO (см. OOP-2).

---
