<div align="center">

# MangoPret (Windows)
Поддержите оригинального разработчика zapret [тут](https://github.com/bol-van/zapret?tab=readme-ov-file#%D0%BF%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%B0%D1%82%D1%8C-%D1%80%D0%B0%D0%B7%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D1%87%D0%B8%D0%BA%D0%B0)

</div>

> [!CAUTION]
> ### ФЕЙКИ
> Мы не распространяем нашу сборку zapret на каких-либо других сайтах или репозиториях. У нас нет зеркала на каком-нибудь "zapretfreenovirus.com".

> [!WARNING]
> ### АНТИВИРУСЫ
> WinDivert и nfqws могут вызвать реакцию антивируса.
> WinDivert/nfqws — это инструмент для перехвата и фильтрации трафика, необходимый для работы zapret.
> Он может использоваться как хорошими, так и плохими программами, но сам по себе не является вирусом.
> Драйвер WinDivert64.sys подписан для возможности загрузки в 64-битное ядро Windows.
>
> В случае проблем с антивирусом добавьте папку с zapret в исключения, либо отключите детектирование PUA.

## Использование

1. **Включите Secure DNS**
   - В Chrome — "Использовать безопасный DNS", выберите поставщика (не "Поставщик по умолчанию")
   - В Windows 11 — настройте DNS через HTTPS в параметрах ОС
   - В Firefox — "Включить DNS через HTTPS", максимальная защита, укажите провайдера вручную (например `https://dns.google/dns-query`)

2. **Запустите `run_gui.bat`** — автоматически установит PyQt6 при необходимости и откроет графический интерфейс.

3. **Или используйте CLI** через `run.bat`:
   ```
   run.bat start "general (EXP)"
   run.bat stop
   run.bat status
   run.bat strategies
   ```

> [!IMPORTANT]
> **Стратегии со временем могут переставать работать.** Если ни одна из стратегий не помогает, создайте новую, изменив параметры существующей.

## Стратегии

В папке `gui/strategies/` находятся 21 файл стратегий (JSON). Каждая стратегия содержит правила для `winws.exe` с параметрами обхода DPI.

## Структура проекта

```
├── run.bat            # CLI-лаунчер
├── run_gui.bat        # GUI-лаунчер (автоустановка PyQt6)
├── gui/
│   ├── main_gui.py    # Точка входа GUI (PyQt6)
│   ├── main.py        # Точка входа CLI
│   ├── core/
│   │   ├── platform.py   # Управление процессом, установка zapret
│   │   ├── strategy.py   # Парсинг и сборка команд стратегий
│   │   ├── config.py     # Конфиг (%APPDATA%\mangopret\config.json)
│   │   └── lists.py      # Управление списками доменов/IP
│   ├── ui/
│   │   ├── main_window.py
│   │   └── tabs/         # Вкладки: Main, Lists, Service, Log
│   └── strategies/       # *.strategy файлы (21 шт.)
├── bin/                  # winws.exe, WinDivert.dll, WinDivert64.sys
├── lists/                # Списки доменов и IP-адресов
└── .service/             # Конфигурация службы Windows
```

## Запуск без GUI (CLI)

```cmd
run.bat install          # установка/обновление zapret
run.bat start "стратегия"  # запуск с указанием стратегии
run.bat stop             # остановка
run.bat fix              # аварийная остановка всех процессов
run.bat status           # статус
run.bat strategies       # список доступных стратегий
run.bat service install  # установка службы Windows
run.bat service start    # запуск службы
run.bat service stop     # остановка службы
run.bat service remove   # удаление службы
run.bat lists update     # обновление списков из GitHub
run.bat diagnostics      # диагностика
```

## Требования

- Windows 7/8/10/11 (x64)
- Python 3 (если не используется портативная сборка)
- Secure DNS (обязательно)

## Сборка релиза

См. `.github/workflows/release.yml`. Архивируются `gui/`, `lists/`, `bin/`, `.service/` и скрипты.
