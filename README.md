# MangoPret
Основано на [zapret](https://github.com/bol-van/zapret) от [bol-van](https://github.com/bol-van).\
Стратегии из [zapret-discord-youtube](https://github.com/flowseal/zapret-discord-youtube) от [Flowseal](https://github.com/flowseal)\
Поддержите разработчика zapret [тут](https://github.com/bol-van/zapret?tab=readme-ov-file#%D0%BF%D0%BE%D0%B4%D0%B4%D0%B5%D1%80%D0%B6%D0%B0%D1%82%D1%8C-%D1%80%D0%B0%D0%B7%D1%80%D0%B0%D0%B1%D0%BE%D1%82%D1%87%D0%B8%D0%BA%D0%B0)
> [!CAUTION]
> ### Фейки
> Мы не распространяем сборку на других сайтах или репозиториях. У нас нет зеркала на «zapretfreenovirus.com».

---

## Быстрый старт

### Linux

```bash
# beta версия
curl -sSL https://raw.githubusercontent.com/AnythingDevelopmentTeam/Mangopret/main/install.sh | sudo bash
```
Стабильная версия
```bash
https://github.com/AnythingDevelopmentTeam/Mangopret/releases/latest
```
# Использование
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
