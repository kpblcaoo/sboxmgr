#!/usr/bin/env python3
"""
Генерация тестовых конфигураций для всех протоколов sing-box.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import random
import string

# Добавляем путь к проекту
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.sboxmgr.models import *


class TestConfigGenerator:
    """Генератор тестовых конфигураций."""
    
    def __init__(self):
        self.test_configs = {}
        self.output_dir = Path("tests/data/singbox_configs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def generate_random_string(self, length: int = 8) -> str:
        """Генерирует случайную строку."""
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
    def generate_random_port(self) -> int:
        """Генерирует случайный порт."""
        return random.randint(10000, 65000)
    
    def generate_random_ip(self) -> str:
        """Генерирует случайный IP адрес."""
        return f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
    
    def generate_shadowsocks_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию Shadowsocks."""
        return {
            "type": "shadowsocks",
            "tag": f"ss-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "method": "aes-256-gcm",
            "password": self.generate_random_string(16)
        }
    
    def generate_vmess_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию VMess."""
        return {
            "type": "vmess",
            "tag": f"vmess-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "uuid": "b831381d-6324-4d53-ad4f-8cda48b30811",
            "security": "auto",
            "alter_id": 0,
            "global_padding": False,
            "authenticated_length": True
        }
    
    def generate_vless_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию VLESS."""
        return {
            "type": "vless",
            "tag": f"vless-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "uuid": "b831381d-6324-4d53-ad4f-8cda48b30811",
            "flow": ""
        }
    
    def generate_trojan_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию Trojan."""
        return {
            "type": "trojan",
            "tag": f"trojan-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "password": self.generate_random_string(16),
            "tls": {
                "enabled": True,
                "server_name": "example.com",
                "insecure": True
            }
        }
    
    def generate_hysteria2_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию Hysteria2."""
        return {
            "type": "hysteria2",
            "tag": f"hysteria2-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "password": self.generate_random_string(16),
            "tls": {
                "enabled": True,
                "server_name": "example.com",
                "insecure": True
            }
        }
    
    def generate_wireguard_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию WireGuard."""
        return {
            "type": "wireguard",
            "tag": f"wg-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "private_key": "YFQoWc0IN9/1Dthy+b9+7VFwXhq5YkxqPLDPluq30Gg=",
            "peer_public_key": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
            "pre_shared_key": "31aIhAPwkhDG+AqgoRRgGkJBuqu1RURFdYQjq4nq7mc=",
            "mtu": 1408
        }
    
    def generate_tuic_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию TUIC."""
        return {
            "type": "tuic",
            "tag": f"tuic-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "uuid": "b831381d-6324-4d53-ad4f-8cda48b30811",
            "password": self.generate_random_string(16),
            "congestion_control": "bbr",
            "udp_relay_mode": "quic",
            "zero_rtt_handshake": False,
            "heartbeat": "10s",
            "tls": {
                "enabled": True,
                "server_name": "example.com",
                "insecure": True
            }
        }
    
    def generate_http_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию HTTP."""
        return {
            "type": "http",
            "tag": f"http-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "username": self.generate_random_string(8),
            "password": self.generate_random_string(16)
        }
    
    def generate_socks_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию SOCKS."""
        return {
            "type": "socks",
            "tag": f"socks-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "username": self.generate_random_string(8),
            "password": self.generate_random_string(16)
        }
    
    def generate_mixed_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию Mixed."""
        return {
            "type": "mixed",
            "tag": f"mixed-{self.generate_random_string()}",
            "listen": "127.0.0.1",
            "listen_port": self.generate_random_port(),
            "users": [
                {
                    "username": self.generate_random_string(8),
                    "password": self.generate_random_string(16)
                }
            ]
        }
    
    def generate_direct_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию Direct."""
        return {
            "type": "direct",
            "tag": f"direct-{self.generate_random_string()}"
        }
    
    def generate_dns_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию DNS."""
        return {
            "type": "dns",
            "tag": f"dns-{self.generate_random_string()}"
        }
    
    def generate_block_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию Block."""
        return {
            "type": "block",
            "tag": f"block-{self.generate_random_string()}"
        }
    
    def generate_selector_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию Selector."""
        return {
            "type": "selector",
            "tag": f"selector-{self.generate_random_string()}",
            "outbounds": ["direct", "block"],
            "default": "direct"
        }
    
    def generate_urltest_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию URLTest."""
        return {
            "type": "urltest",
            "tag": f"urltest-{self.generate_random_string()}",
            "outbounds": ["direct", "block"],
            "url": "https://www.gstatic.com/generate_204",
            "interval": "300s",
            "tolerance": 50
        }
    
    def generate_anytls_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию AnyTLS."""
        return {
            "type": "anytls",
            "tag": f"anytls-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "password": "8JCsPssfgS8tiRwiMlhARg==",
            "tls": {
                "enabled": True,
                "server_name": "example.com",
                "insecure": True
            }
        }
    
    def generate_ssh_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию SSH."""
        return {
            "type": "ssh",
            "tag": f"ssh-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": 22,
            "user": "root",
            "password": "admin"
        }
    
    def generate_tor_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию Tor."""
        return {
            "type": "tor",
            "tag": f"tor-{self.generate_random_string()}",
            "executable_path": "/usr/bin/tor",
            "data_directory": "/tmp/tor-data"
        }
    
    def generate_hysteria_config(self) -> Dict[str, Any]:
        """Генерирует тестовую конфигурацию Hysteria (старая версия)."""
        return {
            "type": "hysteria",
            "tag": f"hysteria-{self.generate_random_string()}",
            "server": self.generate_random_ip(),
            "server_port": self.generate_random_port(),
            "up_mbps": 100,
            "down_mbps": 100,
            "auth_str": "password",
            "tls": {
                "enabled": True,
                "server_name": "example.com",
                "insecure": True
            }
        }
    
    def generate_full_config(self, protocol: str) -> Dict[str, Any]:
        """Генерирует полную конфигурацию sing-box для протокола."""
        # Генерируем outbound конфигурацию
        outbound_generators = {
            'shadowsocks': self.generate_shadowsocks_config,
            'vmess': self.generate_vmess_config,
            'vless': self.generate_vless_config,
            'trojan': self.generate_trojan_config,
            'hysteria2': self.generate_hysteria2_config,
            'wireguard': self.generate_wireguard_config,
            'tuic': self.generate_tuic_config,
            'http': self.generate_http_config,
            'socks': self.generate_socks_config,
            'direct': self.generate_direct_config,
            'dns': self.generate_dns_config,
            'block': self.generate_block_config,
            'selector': self.generate_selector_config,
            'urltest': self.generate_urltest_config,
            'anytls': self.generate_anytls_config,
            'ssh': self.generate_ssh_config,
            'tor': self.generate_tor_config,
            'hysteria': self.generate_hysteria_config,
        }
        
        if protocol not in outbound_generators:
            raise ValueError(f"Неподдерживаемый протокол: {protocol}")
            
        outbound = outbound_generators[protocol]()
        
        # Создаем полную конфигурацию
        config = {
            "log": {
                "level": "info",
                "timestamp": True
            },
            "dns": {
                "servers": [
                    {
                        "tag": "google",
                        "address": "8.8.8.8",
                        "detour": "direct"
                    }
                ]
            },
            "inbounds": [
                {
                    "type": "mixed",
                    "tag": "mixed-in",
                    "listen": "127.0.0.1",
                    "listen_port": 1080
                }
            ],
            "outbounds": [
                outbound,
                {
                    "type": "direct",
                    "tag": "direct"
                },
                {
                    "type": "block",
                    "tag": "block"
                }
            ],
            "route": {
                "rules": [
                    {
                        "protocol": "dns",
                        "outbound": "dns"
                    }
                ]
            }
        }
        
        return config
    
    def generate_all_configs(self) -> Dict[str, Dict[str, Any]]:
        """Генерирует конфигурации для всех протоколов."""
        protocols = [
            'shadowsocks', 'vmess', 'vless', 'trojan', 'hysteria2',
            'wireguard', 'tuic', 'http', 'socks', 'direct', 'dns',
            'block', 'selector', 'urltest', 'anytls', 'ssh', 'tor', 'hysteria'
        ]
        
        for protocol in protocols:
            try:
                config = self.generate_full_config(protocol)
                self.test_configs[protocol] = config
                print(f"✅ Сгенерирована конфигурация для {protocol}")
            except Exception as e:
                print(f"❌ Ошибка генерации {protocol}: {e}")
                
        return self.test_configs
    
    def save_configs(self):
        """Сохраняет все конфигурации в файлы."""
        for protocol, config in self.test_configs.items():
            file_path = self.output_dir / f"{protocol}_test.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"💾 Сохранена конфигурация: {file_path}")
    
    def generate_validation_report(self) -> str:
        """Генерирует отчет о валидации."""
        report = []
        report.append("# Отчет о генерации тестовых конфигураций")
        report.append("")
        report.append(f"Всего сгенерировано конфигураций: {len(self.test_configs)}")
        report.append("")
        
        report.append("## Список конфигураций")
        report.append("")
        report.append("| Протокол | Файл | Статус |")
        report.append("|----------|------|--------|")
        
        for protocol in sorted(self.test_configs.keys()):
            file_path = self.output_dir / f"{protocol}_test.json"
            if file_path.exists():
                status = "✅ Создан"
            else:
                status = "❌ Ошибка"
            report.append(f"| {protocol} | {file_path.name} | {status} |")
            
        return "\n".join(report)


def main():
    """Основная функция."""
    generator = TestConfigGenerator()
    
    print("Генерация тестовых конфигураций sing-box...")
    
    # Генерируем все конфигурации
    generator.generate_all_configs()
    
    # Сохраняем конфигурации
    generator.save_configs()
    
    # Генерируем отчет
    report = generator.generate_validation_report()
    
    # Сохраняем отчет
    report_path = "docs/test_configs_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"\nОтчет сохранен в {report_path}")
    print("\n" + "="*50)
    print(report)


if __name__ == "__main__":
    main() 