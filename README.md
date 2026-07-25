# MangoPret

> **Независимый форк** (ранее — ответвление от zapret-discord-youtube).  
> Полностью переработан: собственный GUI, CLI, система стратегий, менеджер списков.

Поддержите оригинального разработчика zapret: [bol-van/zapret](https://github.com/bol-van/zapret)

> [!CAUTION]
> ### Фейки
> Мы не распространяем сборку на других сайтах или репозиториях. У нас нет зеркала на «zapretfreenovirus.com».

---

## Возможности

| | |
|---|---|
| 🖥️ **GUI** | PyQt6 интерфейс с тёмной, светлой и контрастной темами |
| ⌨️ **CLI** | Полноценное управление через терминал |
| 🧠 **27+ стратегий** | EXP, ALT1–12, FAKE, SPLIT, DISORDER, MULTISPLIT, игровые |
| 🔧 **Мастер стратегий** | Конвертация `.bat` → `.strategy`, автообновление из репозитория |
| 📋 **Редактор списков** | Домены (`list-*.txt`) и IP (`ipset-*.txt`) с split-pane |
| 🔄 **Автообновление** | IPSet, hosts, стратегии — одной командой |
| ⚙️ **Systemd сервис** | Установка, запуск, стоп, автостарт, логи |
| 🧹 **iptables** | NFQUEUE правила, очистка при падении, emergency fix |
| 🪟 **Windows** | Полноценная поддержка WinDivert + WinDivert hide |
| 🔔 **Tray** | Системный трей с быстрыми действиями |
| 🎯 **CLI автодополнение** | Bash/Zsh/Fish (через argcomplete) |
| 📊 **Диагностика** | Проверка конфликтов (BFE, Adguard, прокси) |

---

## Быстрый старт

### Linux

```bash
# GUI (автоустановка зависимостей, повышение прав)
./run_gui.sh

# CLI
sudo ./run.sh start "general (EXP)"
sudo ./run.sh stop
sudo ./run.sh fix               # аварийная очистка iptables
sudo ./run.sh status
sudo ./run.sh strategies
sudo ./run.sh service install
sudo ./run.sh service start
```

### Windows

```cmd
run_gui.bat          # GUI
run.bat start "general (EXP)"
run.bat stop
```

---

## CLI команды

| Команда | Описание |
|---|---|
| `start <стратегия>` | Запустить обход |
| `stop` | Остановить |
| `fix` | Аварийно убить nfqws + очистить iptables |
| `status` | Состояние (процесс, сервис, IPSet) |
| `strategies` | Список доступных стратегий |
| `install` | Установить zapret в `/opt/zapret` (Linux) |
| `update` | Обновить zapret до последней версии |
| `service install\|start\|stop\|remove\|log` | Управление systemd сервисом |
| `lists list\|edit\|update-ipset\|update-hosts\|update-strategies` | Управление списками |
| `autostart enable\|disable\|status` | Автозапуск при входе в систему |
| `diagnostics` | Диагностика конфликтов |
| `convert <input> -o <dir>` | Конвертация `.bat` → `.strategy` |
| `completion bash\|zsh\|fish` | Сгенерировать скрипт автодополнения |

---

## Стратегии

Файлы в `gui/strategies/*.strategy` — JSON с правилами для nfqws/winws.
Если ни одна стратегия не работает, возьмите за основу ближайшую и измените параметры.  
Документация по параметрам: [nfqws](https://github.com/bol-van/zapret/blob/master/docs/readme.md#nfqws)

### Если не работает

1. Убедитесь, что адрес ресурса есть в списках доменов или IP
2. Проверьте другие стратегии — **ALT**, **FAKE** и т.д.
3. Попробуйте полную переустановку
4. Запустите `blockcheck`

---

## Темы

Переключение в настройках GUI или через `config.json` (`theme: dark | light | contrast`).

---

## CLI автодополнение

```bash
pip install mangopret[completion]
./run.sh completion bash > /etc/bash_completion.d/mangopret
./run.sh completion zsh  > /usr/share/zsh/vendor-completions/_mangopret
./run.sh completion fish > ~/.config/fish/completions/mangopret.fish
```

---

## Troubleshooting

### Не работает YouTube

- Настройте Secure DNS
- Отключите блокировщик рекламы
- Пробуйте все стратегии

### Не работает Discord

- Настройте Secure DNS
- Сначала добейтесь работы YouTube на какой-нибудь стратегии
- `service.bat` → `Run Diagnostics` → очистка кэша Discord
- Попробуйте в браузере: https://discord.com/app

### Не работает Telegram

- Используйте [tg-ws-proxy](https://github.com/Flowseal/tg-ws-proxy)
- Или бесплатные MTProto прокси

### Античит ругается на WinDivert

Инструкция: [zapret-win-bundle/windivert-hide](https://github.com/bol-van/zapret-win-bundle/tree/master/windivert-hide)

### Не работают игры

- Game Filter → `disabled`, IPSet Filter → `none`
- Не используйте `ipset any` на постоянной основе
- Добавьте IP адреса игры в `ipset-all.txt`
- Не помогло? Создайте [обсуждение](https://github.com/AnythingDevelopmentTeam/Mangopret/discussions)

---

## Редактирование списков

| Файл | Назначение |
|---|---|
| `list-general-user.txt` | Домены для обхода (поддомены автоматически) |
| `list-exclude-user.txt` | Исключения доменов |
| `ipset-all.txt` | IP и подсети |
| `ipset-exclude-user.txt` | Исключения IP |

Файлы `*-user.txt` создаются автоматически при первом запуске.

---

## Разработка

```bash
pip install -e ".[dev]"
pytest tests/ -v
ruff check
ruff format --check
pre-commit run --all
```

Полная архитектура описана в [AGENTS.md](./AGENTS.md).

---

## Лицензия

MIT — [LICENSE.txt](./LICENSE.txt)

---

## Благодарности

[![Contributors](https://contrib.rocks/image?repo=AnythingDevelopmentTeam/mangopret)](https://github.com/AnythingDevelopmentTeam/mangopret/graphs/contributors)

💖 Отдельная благодарность [bol-van](https://github.com/bol-van) — разработчику [zapret](https://github.com/bol-van/zapret)
