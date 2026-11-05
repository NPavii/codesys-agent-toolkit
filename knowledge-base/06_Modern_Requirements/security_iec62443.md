# Безопасность: IEC 62443 и CODESYS

## IEC 62443 кратко

Семейство стандартов по кибербезопасности IACS/OT. Ключевые элементы:
* **Zones & Conduits** — сегментация сети на зоны по риску; между зонами —
  только разрешённый трафик (default-deny).
* **Security Levels SL 0–4** — целевой уровень (SL-T) назначается по
  последствиям компрометации зоны; достигнутый (SL-A) проверяется аудитом.
* **CSMS** — система управления кибербезопасностью: роли, инвентаризация
  активов, patch/change management, обучение, мониторинг, IR-процедуры.
* Разработчикам: IEC 62443-4-1 (secure development lifecycle) и 4-2
  (требования к компонентам). CODESYS Group декларирует процессы по 62443
  и публикует Security Whitepaper.

## Что даёт CODESYS из коробки (Security in CODESYS, helpme-codesys.com)

* X.509-сертификаты: шифрование исходников, boot application, пакетов и
  коммуникации IDE ↔ PLC.
* Device User Management: пользователи/группы, политика паролей, лимит
  попыток входа, time-limited критичные действия (STOP/RESET).
* Шифрование CDS↔PLC и OPC UA Server; аудит-лог событий; backup/restore;
  экспорт/импорт пользователей устройства.
* **CODESYS Security Agent** (Store, бесплатный аддон 000093) — центральное
  управление security-настройками среды.

## Top-20 Secure PLC Coding Practices (S4 community) — выжимка

1. Валидировать HMI-входы по диапазону (кейс Oldsmar — вода).
2. Отключать неиспользуемые порты/протоколы (attack surface reduction).
3. Логирование/тренды/мониторинг cycle time и памяти — детект аномалий.
4. Парные входы (не может быть и Open, и Closed), индирекции.
5. Integrity checks конфигурации, регистров, флагов.

## Практические правила для наших проектов

| Правило | Реализация |
|---|---|
| Учётки на ПЛК, не «пустой рантайм» | User Management + сертификаты, особенно на объекте |
| Шифрование OPC UA | Сертификаты, SecurityPolicy Basic256Sha256+ |
| Минимум сервисов | Оставить только нужные порты; MQTT/REST — через шлюз/DMZ |
| Аудит | Audit log + журнал PackML StopReason/Alarm (связка с OEE) |
| Уязвимости библиотек | Следить CISA ICS advisories (пример: OSCAT CVE-2024-6876 — см. [standard_libraries](../02_Libraries/standard_libraries.md)) |
| Секреты в коде | Никогда: пароли/IP — в отдельных GVL-конфигах вне репозитория; в MCP-пайплайне — только через env |

## TODO

* [ ] CODESYS Security Whitepaper (PDF) — скачать в `Library/_ref/`.
* [ ] Практика: включить User Management + сертификаты на тестовом SoftPLC.
