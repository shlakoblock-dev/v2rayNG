import requests
import re
import json
import socket
import base64
import time
import concurrent.futures
from urllib.parse import urlparse, unquote, parse_qs

URLS = [
    "https://raw.githubusercontent.com/PizdukMod/PizdukVPN/refs/heads/main/sub",
    "https://raw.githubusercontent.com/flaafix/AetrisVPN-black-list/refs/heads/main/configs.txt",
    "https://raw.githubusercontent.com/s0ulcoil/HavenVPN/refs/heads/main/Haven",
    "https://raw.githubusercontent.com/korol5028/korol-vpn/main/Pohyu.txt",
    "https://raw.githubusercontent.com/Buffetbarko/Universal-Proxy-Config-Parser-/main/whitelist_vpn.txt"
]

SUB_NAME = "Sлiвы VPN"
TIMEOUT = 1.0  # Ждем ответа сокета до 1 сек
MAX_PING_MS = 500 # Фильтр по пингу (в мс)
MAX_SERVERS_TOTAL = 25
MAX_SERVERS_PER_COUNTRY = 3

def log_progress(msg):
    print(msg)
    try:
        from java import jclass
        Log = jclass("android.util.Log")
        Log.d("SLIVY_VPN", msg)
    except:
        pass

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

def get_country_flags(name):
    flags = re.findall(r'[\U0001F1E6-\U0001F1FF]{2}', name)
    return tuple(flags) if flags else None

def get_host_port(config):
    try:
        scheme = config.split("://", 1)[0].lower()
        if scheme == "vmess":
            d = json.loads(b64decode_safe(config[8:]).decode('utf-8', 'ignore'))
            return d.get("add"), int(d.get("port"))
        u = urlparse(config)
        if u.hostname and u.port:
            return u.hostname, u.port
        if scheme == "ss":
            body = config[5:].split("#")[0].split("?")[0]
            if "@" in body:
                hostport = body.rsplit("@", 1)[1]
                h, p = hostport.rsplit(":", 1)
                return h.strip("[]"), int(p)
    except: pass
    return None, None

def check_tcp_ping(host, port):
    """Проверяем пинг через TCP (работает в Android без root)"""
    if not host or not port: return None
    try:
        t = time.perf_counter()
        with socket.create_connection((host, int(port)), timeout=TIMEOUT):
            ms = int((time.perf_counter() - t) * 1000)
            return ms
    except Exception:
        return None

def run():
    log_progress("Начинаем сбор конфигов...")
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
            log_progress(f"Ошибка загрузки {url}: {e}")

    # Дедупликация
    uniq = {}
    for c in all_configs:
        key = c if c.lower().startswith("vmess://") else c.split("#")[0]
        uniq.setdefault(key, c)
    all_configs = list(uniq.values())
    log_progress(f"Всего уникальных конфигов: {len(all_configs)}")

    # Параллельная проверка TCP
    log_progress("Проверяем пинг (TCP)...")
    results = []
    
    def process_config(c):
        host, port = get_host_port(c)
        ping = check_tcp_ping(host, port)
        if ping is not None and ping <= MAX_PING_MS:
            name = get_name(c)
            flags = get_country_flags(name)
            if flags:
                return (c, ping, flags, name)
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        for res in executor.map(process_config, all_configs):
            if res: results.append(res)

    log_progress(f"Прошло фильтр: {len(results)}")

    # Сортировка по пингу
    results.sort(key=lambda x: x[1])

    # Лимиты
    final = []
    country_counts = {}
    skipped = []
    
    for c, ping, flags, name in results:
        if len(final) >= MAX_SERVERS_TOTAL: break
        cnt = country_counts.get(flags, 0)
        if cnt >= MAX_SERVERS_PER_COUNTRY:
            skipped.append((c, ping, flags, name))
            continue
        final.append((c, ping, flags, name))
        country_counts[flags] = cnt + 1

    # Добор
    if len(final) < MAX_SERVERS_TOTAL:
        needed = MAX_SERVERS_TOTAL - len(final)
        final.extend(skipped[:needed])
        final.sort(key=lambda x: x[1])

    # Формирование подписки
    lines = []
    for c, ping, flags, orig_name in final:
        country = orig_name.split("•")[0].strip() if "•" in orig_name else orig_name
        new_name = f"{country} • {SUB_NAME}"
        
        if c.lower().startswith("vmess://"):
            try:
                d = json.loads(b64decode_safe(c[8:]).decode('utf-8', 'ignore'))
                d["ps"] = new_name
                c = "vmess://" + base64.b64encode(json.dumps(d, ensure_ascii=False).encode('utf-8')).decode()
            except: pass
        else:
            c = c.split("#")[0] + "#" + requests.utils.quote(new_name)
            
        lines.append(c)

    log_progress(f"Готово! Собрано {len(lines)} серверов.")
    return "\n".join(lines)