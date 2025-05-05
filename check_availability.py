#!/usr/bin/env python3
"""
Модуль для проверки доступности серверов VPN для sing-box.

Проверяет доступность сервера одним из трёх способов:
- Без прокси: TCP-соединение (для update-singbox.py --check-availability).
- С прокси: сравнение внешнего IP без прокси и через SOCKS5 (127.0.0.1:1080).
- С прокси и --check-node: проверка доступности конкретного узла через SOCKS5.
Использует curl для проверки IP или узла через SOCKS5.

Использование:
    python3 check_availability.py --server <host> --port <port> [--timeout <seconds>] [--proxy <host:port>] [--check-node] [--verbose]
    Пример: python3 check_availability.py --server example.com --port 443 --timeout 5
    Пример: python3 check_availability.py --server example.com --port 443 --proxy 127.0.0.1:1080
    Пример: python3 check_availability.py --server example.com --port 443 --proxy http://127.0.0.1:1080 --check-node

Примечание:
    Аргумент --proxy ожидает формат host:port (например, 127.0.0.1:1080) или http://host:port.
    Формат https://host:port не поддерживается, так как SOCKS5 не использует TLS.

Требования:
    Утилита curl должна быть установлена в системе.
"""
import argparse
import socket
import subprocess
import shutil

def get_external_ip(proxy: str = None, timeout: float = 5.0, verbose: bool = False) -> str | None:
    """
    Получает внешний IP через сервисы http://api.ipify.org или http://ifconfig.me/ip (фоллбэк).

    Аргументы:
        proxy: Адрес прокси (host:port или http://host:port). Если указан, использует --socks5.
        timeout: Таймаут в секундах.
        verbose: Если True, выводит дополнительные сообщения для отладки.

    Возвращает:
        Строку с IP или None при ошибке.
    """
    if not shutil.which("curl"):
        print("[DEBUG] Ошибка: утилита curl не найдена в системе")
        return None

    services = ["http://api.ipify.org", "http://ifconfig.me/ip"]
    for service in services:
        cmd = ["curl", "-s", "--max-time", str(timeout), service]
        if proxy:
            proxy_host = proxy.replace("http://", "").replace("https://", "")
            cmd.extend(["--socks5", proxy_host])

        if verbose:
            print(f"[DEBUG] Команда: {' '.join(cmd)}")  # Логируем команду
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            ip = result.stdout.strip()
            if ip:
                return ip
        except subprocess.CalledProcessError:
            continue
    return None

def check_node_availability(server: str, port: int, proxy: str, timeout: float = 5.0, verbose: bool = False) -> bool:
    """
    Проверяет доступность конкретного узла через прокси с помощью curl.

    Аргументы:
        server: Хост узла (IP или домен).
        port: Порт узла.
        proxy: Адрес прокси (host:port или http://host:port).
        timeout: Таймаут в секундах.
        verbose: Если True, выводит дополнительные сообщения для отладки.

    Возвращает:
        True, если узел доступен через прокси, иначе False.
    """
    if not shutil.which("curl"):
        print("[DEBUG] Ошибка: утилита curl не найдена в системе")
        return False

    proxy_host = proxy.replace("http://", "").replace("https://", "")
    cmd = [
        "curl", "-s", "-L", "--max-time", str(timeout),
        "--socks5", proxy_host,
        f"https://{server}:{port}"
    ]

    if verbose:
        print(f"[DEBUG] Команда: {' '.join(cmd)}")  # Логируем команду
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        return False

def check_server_availability(server: str, port: int, timeout: float = 5.0, proxy: str = None, check_node: bool = False, verbose: bool = False) -> bool:
    """
    Проверяет доступность сервера.

    Без прокси: проверяет TCP-соединение.
    С прокси и --check-node: проверяет доступность узла через SOCKS5.
    С прокси без --check-node: сравнивает внешний IP без прокси и через SOCKS5.
    Если IP разные или узел доступен, сервер считается доступным.

    Аргументы:
        server: Хост сервера (IP или домен).
        port: Порт сервера.
        timeout: Таймаут в секундах (по умолчанию 5.0).
        proxy: Адрес прокси (host:port или http://host:port). Если None, проверяется TCP.
        check_node: Если True, проверяет доступность узла через прокси.
        verbose: Если True, выводит дополнительные сообщения для отладки.

    Возвращает:
        True, если сервер доступен, иначе False.
    """
    if proxy:
        if proxy.startswith("https://"):
            print("[DEBUG] Ошибка: --proxy не поддерживает https://, используйте host:port или http://host:port")
            return False

        if check_node:
            # Проверка конкретного узла через прокси
            result = check_node_availability(server, port, proxy, timeout, verbose)
            print(f"[DEBUG] Узел {server}:{port} {'доступен' if result else 'недоступен'} через прокси {proxy}")
            return result
        else:
            # Проверка через прокси: сравнение IP
            no_proxy_ip = get_external_ip(timeout=timeout, verbose=verbose)
            proxy_ip = get_external_ip(proxy=proxy, timeout=timeout, verbose=verbose)
            
            if no_proxy_ip is None:
                print("[DEBUG] Не удалось получить IP без прокси")
                return False
            if proxy_ip is None:
                print(f"[DEBUG] Не удалось получить IP через прокси {proxy}")
                return False
            if no_proxy_ip == proxy_ip:
                print(f"[DEBUG] IP не изменился: {no_proxy_ip} (без прокси) = {proxy_ip} (через прокси)")
                return False
            
            print(f"[DEBUG] IP изменился: {no_proxy_ip} (без прокси) -> {proxy_ip} (через прокси)")
            return True
    else:
        # Проверка TCP-соединения только если нет proxy
        if not server or not port:
            print("[DEBUG] Сервер и порт обязательны, если прокси не используется")
            return False

        try:
            with socket.create_connection((server, port), timeout=timeout):
                return True
        except (socket.timeout, ConnectionRefusedError):
            return False

def main():
    """CLI-интерфейс для проверки доступности сервера."""
    parser = argparse.ArgumentParser(description="Проверка доступности сервера VPN")
    parser.add_argument("--server", required=False, help="Хост сервера (IP или домен)")
    parser.add_argument("--port", type=int, required=False, help="Порт сервера")
    parser.add_argument("--timeout", type=float, default=5.0, help="Таймаут в секундах")
    parser.add_argument("--proxy", help="Адрес прокси (host:port или http://host:port, например, 127.0.0.1:1080)")
    parser.add_argument("--check-node", action="store_true", help="Проверять доступность узла через прокси")
    parser.add_argument("--verbose", action="store_true", help="Выводить подробные сообщения для отладки")
    args = parser.parse_args()

    if args.proxy:
        result = check_server_availability(args.server, args.port, args.timeout, args.proxy, args.check_node, args.verbose)
        print(f"[DEBUG] Сервер {args.server}:{args.port} {'доступен' if result else 'недоступен'}")
        exit(0 if result else 1)
    else:
        # Проверка внешнего IP, если не указан сервер и порт
        result = get_external_ip(proxy=args.proxy, timeout=args.timeout, verbose=args.verbose)
        if result:
            print(f"[DEBUG] Внешний IP: {result}")
            exit(0)
        else:
            print("[DEBUG] Не удалось получить внешний IP")
            exit(1)

if __name__ == "__main__":
    main()
