import requests
import re
import json
import base64
from urllib.parse import unquote

URLS = [
    "https://raw.githubusercontent.com/PizdukMod/PizdukVPN/refs/heads/main/sub",
    "https://raw.githubusercontent.com/flaafix/AetrisVPN-black-list/refs/heads/main/configs.txt",
    "https://raw.githubusercontent.com/s0ulcoil/HavenVPN/refs/heads/main/Haven",
    "https://raw.githubusercontent.com/korol5028/korol-vpn/main/Pohyu.txt",
    "https://raw.githubusercontent.com/Buffetbarko/Universal-Proxy-Config-Parser-/main/whitelist_vpn.txt"
]

SUB_NAME = "Sлiвы VPN"
PATTERN = r'((?:vmess|vless|trojan|ss)://[^\s]+)'

def b64decode_safe(s):
    s = s.strip().replace('-', '+').replace('_', '/').rstrip('=')
    s += '=' * (-len(s) % 4)
    return base64.b64decode(s, validate=True)

def get_name(config):
    try:
        if config.lower().startswith("vmess://"):
            return json.loads(b64decode_safe(config[8:]).decode('utf-8', 'ignore')).get("ps", "")
        if "#" in config: return unquote(config.split("#", 1)[1])
    except: pass
    return ""

def run():
    print("Downloading configs...")
    all_configs = []
    for url in URLS:
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            text = r.text.strip()
            if not re.search(PATTERN, text):
                try: text = b64decode_safe(re.sub(r'\s+', '', text)).decode('utf-8', 'ignore')
                except: pass
            configs = [c.rstrip('",\'<>') for c in re.findall(PATTERN, text, re.IGNORECASE)]
            all_configs.extend(configs)
        except Exception as e:
            print(f"Error {url}: {e}")

    # Убираем дубликаты
    uniq = {}
    for c in all_configs:
        key = c if c.lower().startswith("vmess://") else c.split("#")[0]
        uniq.setdefault(key, c)
    all_configs = list(uniq.values())
    
    print(f"Total configs: {len(all_configs)}")
    
    # Сразу возвращаем строку (без проверки пинга)
    return "\n".join(all_configs)