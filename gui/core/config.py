import os
import json
from pathlib import Path
from typing import Any
from core.log import get_logger

logger = get_logger(__name__)


# Mangopret: весь код ниже — система настроек программы
# Настройки хранятся в ~/.config/mangopret/config.json

class Config:
    # Словарь со значениями по умолчанию (как мы учили — ключ: значение)
    # Если в config.json нет какого-то ключа, берётся отсюда
    _defaults: dict[str, Any] = {
        "ipset_mode": "loaded",     # режим ipset: none / loaded / any
        "check_updates": True,      # проверять обновления при запуске
        "last_strategy": "",        # какая стратегия была выбрана в прошлый раз
        "minimize_to_tray": True,   # сворачивать в трей вместо закрытия
        "start_minimized": False,   # запускать сразу свёрнутым
        "auto_start": False,        # автоматически запускать стратегию при старте
        "theme": "system",          # тема: system / dark / light
        "nfqueue_num": "200",       # номер очереди NFQUEUE для iptables
        "linux_zapret_path": "",    # путь к zapret на Linux
    }

    # __init__ — это «конструктор», вызывается когда создаётся Config
    # Mangopret: создаётся один раз при запуске GUI или CLI
    def __init__(self, config_dir: str) -> None:
        self.config_dir = Path(config_dir)                          # папка с настройками
        self.config_file = self.config_dir / "config.json"          # путь к файлу
        self._data = dict(self._defaults)                           # берём defaults
        self.load()                                                 # читаем из файла

    # Читает config.json с диска и обновляет _data
    def load(self) -> None:
        if self.config_file.exists():                               # если файл есть
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    saved = json.load(f)                            # превращаем JSON в словарь
                self._data.update(saved)                            # обновляем defaults тем что в файле
            except Exception as exc:
                logger.warning("Failed to load config from %s: %s", self.config_file, exc)

    # Сохраняет _data в config.json
    def save(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)          # создаём папку если нет
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)  # записываем красиво

    # Получить настройку по ключу
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    # Установить настройку и сразу сохранить
    def set(self, key: str, value: Any) -> None:
        self._data[key] = value                                     # кладём в словарь
        self.save()                                                 # пишем на диск

    # А это «магические методы» — позволяют писать config["key"] вместо config.get("key")
    def __getitem__(self, key: str) -> Any:
        return self._data.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    # Mangopret: читает ipset-all.txt и определяет, какой сейчас режим
    def get_ipset_mode(self, lists_dir: str) -> str:
        ipset_file = Path(lists_dir) / "ipset-all.txt"
        if not ipset_file.exists():
            return "none"                                           # файла нет — режим none
        try:
            size = ipset_file.stat().st_size                        # размер файла в байтах
            if size < 100:                                          # если меньше 100 байт — это заглушка
                content = ipset_file.read_text(encoding="utf-8").strip()
                if "203.0.113.113" in content:                      # специальный IP-адрес-заглушка
                    return "none"
                if content == "":
                    return "any"
                return "loaded"
        except Exception as exc:
            logger.warning("Failed to read ipset file %s: %s", ipset_file, exc)
            return "none"
        return "none"

    # Mangopret: переключает режимы ipset подменой файлов
    def set_ipset_mode(self, mode: str, lists_dir: str) -> None:
        ipset_file = Path(lists_dir) / "ipset-all.txt"              # основной файл
        backup_file = Path(lists_dir) / "ipset-all.txt.backup"      # бекап

        if mode == "none":                                          # режим «выключено»
            if ipset_file.exists() and ipset_file.stat().st_size > 100:
                content = ipset_file.read_text(encoding="utf-8")
                if "203.0.113.113" not in content:                  # если там ещё не заглушка
                    if backup_file.exists():
                        backup_file.unlink()                        # удаляем старый бекап
                    ipset_file.rename(backup_file)                  # переименовываем в .backup
                    ipset_file.write_text("203.0.113.113/32\n", encoding="utf-8")  # пишем заглушку
        elif mode == "any":                                         # режим «все IP»
            if ipset_file.exists() and ipset_file.stat().st_size > 100:
                content = ipset_file.read_text(encoding="utf-8")
                if "203.0.113.113" not in content:
                    if backup_file.exists():
                        backup_file.unlink()
                    ipset_file.rename(backup_file)
                    ipset_file.write_text("", encoding="utf-8")     # пустой файл = разрешить все
        elif mode == "loaded":                                      # режим «загруженный список»
            if backup_file.exists() and backup_file.stat().st_size > 100:
                if ipset_file.exists():
                    ipset_file.unlink()                             # удаляем текущий
                backup_file.rename(ipset_file)                      # восстанавливаем из бекапа

        self._data["ipset_mode"] = mode                             # запоминаем режим
        self.save()
