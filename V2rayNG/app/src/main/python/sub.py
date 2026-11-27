import requests
import re
import os
import sys
import json
import time
import socket
import base64
import shutil
import tempfile
import subprocess
from urllib.parse import urlparse, unquote, parse_qs, quote
from concurrent.futures import ThreadPoolExecutor

URLS = [
    "https://raw.githubusercontent.com/PizdukMod/PizdukVPN/refs/heads/main/sub",
    "https://raw.githubusercontent.com/flaafix/AetrisVPN-black-list/refs/heads/main/configs.txt",
    "https://raw.githubusercontent.com/s0ulcoil/HavenVPN/refs/heads/main/Haven",
    "https://raw.githubusercontent.com/korol5028/korol-vpn/main/Pohyu.txt",
    "https://raw.githubusercontent.com/Buffetbarko/Universal-Proxy-Config-Parser-/main/whitelist_vpn.txt"
]

SUB_NAME = "Sлiвы VPN"
TIMEOUT = 0.5
BLACKLIST = ["cloudflare", "chatgpt", "openai", "google", "microsoft", "amazon", "aws", "cdn"]

XRAY_PATH = os.environ.get("XRAY_PATH") or shutil.which("xray") or "./xray"
PING_URL = "http://www.gstatic.com/generate_204"
PING_TIMEOUT = 2.0
PING_TRIES = 2
MAX_PING_MS = 500

BATCH_SIZE = 250
BASE_PORT = 21000
PING_THREADS = 100
KEEP_FAILED = False

MAX_SERVERS_TOTAL = 25
MAX_SERVERS_PER_COUNTRY = 3

COUNTRY_NAMES = {
    "🇷🇺": "Россия", "🇺🇸": "США", "🇩🇪": "Германия", "🇳🇱": "Нидерланды", "🇫🇷": "Франция",
    "🇬🇧": "Великобритания", "🇯🇵": "Япония", "🇰🇷": "Корея", "🇨🇳": "Китай", "🇭🇰": "Гонконг",
    "🇸🇬": "Сингапур", "🇨🇦": "Канада", "🇦🇺": "Австралия", "🇧🇷": "Бразилия", "🇮🇳": "Индия",
    "🇹🇷": "Турция", "🇮🇹": "Италия", "🇪🇸": "Испания", "🇵🇱": "Польша", "🇺🇦": "Украина",
    "🇰🇿": "Казахстан", "🇧🇾": "Беларусь", "🇫🇮": "Финляндия", "🇸🇪": "Швеция", "🇳🇴": "Норвегия",
    "🇩🇰": "Дания", "🇨🇭": "Швейцария", "🇦🇹": "Австрия", "🇧🇪": "Бельгия", "🇮🇪": "Ирландия",
    "🇵🇹": "Португалия", "🇬🇷": "Греция", "🇨🇿": "Чехия", "🇸🇰": "Словакия", "🇭🇺": "Венгрия",
    "🇷🇴": "Румыния", "🇧🇬": "Болгария", "🇷🇸": "Сербия", "🇭🇷": "Хорватия", "🇸🇮": "Словения",
    "🇪🇪": "Эстония", "🇱🇻": "Латвия", "🇱🇹": "Литва", "🇲🇩": "Молдова", "🇬🇪": "Грузия",
    "🇦🇲": "Армения", "🇦🇿": "Азербайджан", "🇺🇿": "Узбекистан", "🇰🇬": "Киргизия", "🇹🇯": "Таджикистан",
    "🇹🇲": "Туркменистан", "🇲🇳": "Монголия", "🇻🇳": "Вьетнам", "🇹🇭": "Таиланд", "🇮🇩": "Индонезия",
    "🇲🇾": "Малайзия", "🇵🇭": "Филиппины", "🇵🇰": "Пакистан", "🇧🇩": "Бангладеш", "🇱🇰": "Шри-Ланка",
    "🇳🇵": "Непал", "🇦🇫": "Афганистан", "🇮🇷": "Иран", "🇮🇶": "Ирак", "🇸🇾": "Сирия",
    "🇱🇧": "Ливан", "🇮🇱": "Израиль", "🇯🇴": "Иордания", "🇸🇦": "Саудовская Аравия", "🇦🇪": "ОАЭ",
    "🇶🇦": "Катар", "🇰🇼": "Кувейт", "🇧🇭": "Бахрейн", "🇴🇲": "Оман", "🇾🇪": "Йемен",
    "🇪🇬": "Египет", "🇲🇦": "Марокко", "🇩🇿": "Алжир", "🇹🇳": "Тунис", "🇱🇾": "Ливия",
    "🇸🇩": "Судан", "🇪🇹": "Эфиопия", "🇰🇪": "Кения", "🇳🇬": "Нигерия", "🇬🇭": "Гана",
    "🇿🇦": "ЮАР", "🇦🇷": "Аргентина", "🇨🇱": "Чили", "🇨🇴": "Колумбия", "🇵🇪": "Перу",
    "🇻🇪": "Венесуэла", "🇪🇨": "Эквадор", "🇺🇾": "Уругвай", "🇵🇾": "Парагвай", "🇧🇴": "Боливия",
    "🇲🇽": "Мексика", "🇨🇺": "Куба", "🇩🇴": "Доминикана", "🇵🇦": "Панама", "🇨🇷": "Коста-Рика",
    "🇬🇹": "Гватемала", "🇭🇳": "Гондурас", "🇸🇻": "Сальвадор", "🇳🇮": "Никарагуа", "🇭🇹": "Гаити",
    "🇯🇲": "Ямайка", "🇹🇹": "Тринидад и Тобаго", "🇧🇸": "Багамы", "🇧🇧": "Барбадос", "🇧🇿": "Белиз",
    "🇳🇿": "Новая Зеландия", "🇫🇯": "Фиджи", "🇵🇬": "Папуа-Новая Гвинея", "🇸🇧": "Соломоновы о-ва",
    "🇻🇺": "Вануату", "🇼🇸": "Самоа", "🇹🇴": "Тонга", "🇰🇮": "Кирибати", "🇲🇭": "Маршалловы о-ва",
    "🇫🇲": "Микронезия", "🇵🇼": "Палау", "🇳🇷": "Науру", "🇹🇻": "Тувалу", "🇨🇰": "О-ва Кука",
    "🇳🇺": "Ниуэ", "🇵🇳": "Питкэрн", "🇹🇰": "Токелау", "🇪🇺": "Евросоюз", "🇺🇳": "ООН"
}

SS_METHODS = {"aes-128-gcm", "aes-256-gcm", "chacha20-ietf-poly1305", "chacha20-poly1305",
              "xchacha20-poly1305", "xchacha20-ietf-poly1305", "2022-blake3-aes-128-gcm",
              "2022-blake3-aes-256-gcm", "2022-blake3-chacha20-poly1305", "none", "plain"}

PATTERN = r'((?:vmess|vless|trojan|ss)://[^\s]+)'

def log_progress(msg):
    print(msg)
    try:
        from java import jclass
        Log = jclass("android.util.Log")
        Log.d("SLIVY_VPN", msg)
    except:
        pass

def ensure_xray():
    global XRAY_PATH
    if os.path.isfile(XRAY_PATH) or shutil.which(XRAY_PATH):
        return True
    import zipfile, platform
    system, machine = platform.system(), platform.machine().lower()
    arm = machine in ("aarch64", "arm64", "armv8l")
    if "com.termux" in os.environ.get("PREFIX", "") or "ANDROID_ROOT" in os.environ:
        plat = "android-arm64-v8a"
    elif system == "Windows": plat = "windows-64"
    elif system == "Darwin": plat = "macos-arm64-v8a" if arm else "macos-64"
    else: plat = "linux-arm64-v8a" if arm else "linux-64"
    exe = "xray.exe" if system == "Windows" else "xray"
    url = f"https://github.com/XTLS/Xray-core/releases/latest/download/Xray-{plat}.zip"
    dest = os.path.join(tempfile.gettempdir(), "xray-core")
    os.makedirs(dest, exist_ok=True)
    zpath = os.path.join(dest, "xray.zip")
    try:
        log_progress(f"Скачиваем xray: {url}")
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        with open(zpath, "wb") as f: f.write(r.content)
        with zipfile.ZipFile(zpath) as z: z.extractall(dest)
        XRAY_PATH = os.path.join(dest, exe)
        if system != "Windows": os.chmod(XRAY_PATH, 0o755)
        return os.path.isfile(XRAY_PATH)
    except Exception as e:
        log_progress(f"Не удалось скачать xray: {e}")
        return False

def b64decode_safe(s):
    s = s.strip().replace('-', '+').replace('_', '/').rstrip('=')
    s += '=' * (-len(s) % 4)
    return base64.b64decode(s, validate=True)

def fetch_content(url):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        text = r.text.strip()
        if re.search(PATTERN, text, re.IGNORECASE): return text
        try: return b64decode_safe(re.sub(r'\s+', '', text)).decode('utf-8', errors='ignore')
        except: return text
    except Exception as e:
        log_progress(f"Ошибка загрузки {url}: {e}")
        return ""

def extract_configs(text):
    return [c.rstrip('",\'<>') for c in re.findall(PATTERN, text, re.IGNORECASE)]

def extract_flags_from_name(name):
    return re.compile(r'[\U0001F1E6-\U0001F1FF]{2}').findall(name)

def get_country_name(flag_emoji):
    return COUNTRY_NAMES.get(flag_emoji, None)

def get_name(config):
    try:
        if config.lower().startswith("vmess://"):
            return json.loads(b64decode_safe(config[8:]).decode('utf-8', 'ignore')).get("ps", "")
        if "#" in config: return unquote(config.split("#", 1)[1])
    except: pass
    return ""

def rename_config(config, name):
    if config.lower().startswith("vmess://"):
        data = json.loads(b64decode_safe(config[8:]).decode('utf-8', 'ignore'))
        data["ps"] = name
        return "vmess://" + base64.b64encode(json.dumps(data, ensure_ascii=False).encode('utf-8')).decode()
    return config.split("#")[0] + "#" + quote(name)

def check_port(host, port):
    if not host or not port: return False
    try:
        with socket.create_connection((host, int(port)), timeout=TIMEOUT):
            return True
    except: return False

def build_stream(p, address):
    net = (p.get("type") or "tcp").lower()
    net = {"none": "tcp", "raw": "tcp", "http": "h2", "splithttp": "xhttp", "mkcp": "kcp"}.get(net, net)
    if net not in ("tcp", "ws", "grpc", "httpupgrade", "xhttp", "kcp", "h2"): raise ValueError(f"unsupported network {net}")

    st = {"network": net}
    sec = (p.get("security") or "none").lower()
    host_hdr = p.get("host") or ""
    path = p.get("path") or ""

    if sec == "tls":
        tls = {"serverName": p.get("sni") or host_hdr or address}
        if p.get("fp"): tls["fingerprint"] = p["fp"]
        if p.get("alpn"): tls["alpn"] = [a for a in p["alpn"].split(",") if a]
        if str(p.get("allowInsecure", "")).lower() in ("1", "true"): raise ValueError("allowInsecure removed")
        st["security"] = "tls"
        st["tlsSettings"] = tls
    elif sec == "reality":
        if not p.get("pbk"): raise ValueError("reality without pbk")
        st["security"] = "reality"
        st["realitySettings"] = {
            "serverName": p.get("sni") or address, "fingerprint": p.get("fp") or "chrome",
            "publicKey": p["pbk"], "shortId": p.get("sid", ""), "spiderX": p.get("spx", ""),
        }
    elif sec != "none": raise ValueError(f"unsupported security {sec}")

    if net == "tcp":
        if (p.get("headerType") or "none") == "http":
            st["tcpSettings"] = {"header": {"type": "http", "request": {"path": [path or "/"], "headers": {"Host": [h for h in host_hdr.split(",") if h]}}}}
    elif net == "ws":
        ws = {"path": path or "/"}
        if host_hdr: ws["headers"] = {"Host": host_hdr}
        st["wsSettings"] = ws
    elif net == "grpc": st["grpcSettings"] = {"serviceName": p.get("service") or "", "multiMode": p.get("mode") == "multi"}
    elif net == "httpupgrade":
        hu = {"path": path or "/"}
        if host_hdr: hu["host"] = host_hdr
        st["httpupgradeSettings"] = hu
    elif net == "xhttp":
        xs = {"path": path or "/"}
        if host_hdr: xs["host"] = host_hdr
        if p.get("mode"): xs["mode"] = p["mode"]
        if p.get("extra"):
            try: xs["extra"] = json.loads(p["extra"])
            except: pass
        st["xhttpSettings"] = xs
    elif net == "kcp":
        kcp = {"header": {"type": p.get("headerType") or "none"}}
        if p.get("seed"): kcp["seed"] = p["seed"]
        st["kcpSettings"] = kcp
    elif net == "h2": st["httpSettings"] = {"path": path or "/", "host": [h for h in host_hdr.split(",") if h]}
    return st

def _query_dict(parsed):
    q = {k: v[0] for k, v in parse_qs(parsed.query).items()}
    q["service"] = q.get("serviceName") or q.get("service") or ""
    q["allowInsecure"] = q.get("allowInsecure") or q.get("insecure") or ""
    return q

def parse_vless(config):
    u = urlparse(config)
    host, port = u.hostname, u.port
    if not (u.username and host and port): return None
    q = _query_dict(u)
    q["type"] = q.get("type") or "tcp"
    if (q.get("security") or "none").lower() == "none" and (q.get("encryption") or "none") == "none": return None
    user = {"id": unquote(u.username), "encryption": q.get("encryption") or "none"}
    if q.get("flow"): user["flow"] = q["flow"]
    ob = {"protocol": "vless", "settings": {"vnext": [{"address": host, "port": port, "users": [user]}]}, "streamSettings": build_stream(q, host)}
    return ob, host, port, ob["streamSettings"]["network"]

def parse_trojan(config):
    u = urlparse(config)
    host, port = u.hostname, u.port
    if not (u.username and host and port): return None
    q = _query_dict(u)
    q["type"] = q.get("type") or "tcp"
    q["security"] = q.get("security") or "tls"
    ob = {"protocol": "trojan", "settings": {"servers": [{"address": host, "port": port, "password": unquote(u.username)}]}, "streamSettings": build_stream(q, host)}
    return ob, host, port, ob["streamSettings"]["network"]

def parse_vmess(config):
    d = json.loads(b64decode_safe(config[8:]).decode('utf-8', 'ignore'))
    host, port, uid = d.get("add"), int(d.get("port")), d.get("id")
    if not (host and port and uid): return None
    net = d.get("net") or "tcp"
    p = {"type": net, "security": "tls" if str(d.get("tls", "")).lower() == "tls" else "none", "sni": d.get("sni"), "host": d.get("host"), "path": d.get("path"), "alpn": d.get("alpn"), "fp": d.get("fp"), "headerType": d.get("type"), "service": d.get("path") if net == "grpc" else "", "mode": d.get("mode")}
    ob = {"protocol": "vmess", "settings": {"vnext": [{"address": host, "port": port, "users": [{"id": uid, "alterId": int(d.get("aid") or 0), "security": d.get("scy") or "auto"}]}]}, "streamSettings": build_stream(p, host)}
    return ob, host, port, ob["streamSettings"]["network"]

def parse_ss(config):
    body = config[5:].split("#")[0]
    query = ""
    if "?" in body: body, query = body.split("?", 1)
    if "plugin=" in query: return None
    body = body.rstrip("/")
    if "@" in body:
        userinfo, hostport = body.rsplit("@", 1)
        try: cred = b64decode_safe(userinfo).decode()
        except: cred = unquote(userinfo)
        if ":" not in cred: cred = unquote(userinfo)
    else:
        dec = b64decode_safe(body).decode()
        cred, hostport = dec.rsplit("@", 1)
    method, password = cred.split(":", 1)
    if method.lower() not in SS_METHODS: return None
    host, port = hostport.rsplit(":", 1)
    host, port = host.strip("[]"), int(port)
    ob = {"protocol": "shadowsocks", "settings": {"servers": [{"address": host, "port": port, "method": method, "password": password}]}}
    return ob, host, port, "tcp"

def parse_config(config):
    try:
        scheme = config.split("://", 1)[0].lower()
        if scheme == "vless": return parse_vless(config)
        if scheme == "vmess": return parse_vmess(config)
        if scheme == "trojan": return parse_trojan(config)
        if scheme == "ss": return parse_ss(config)
    except: pass
    return None

def make_xray_config(batch):
    inbounds, outbounds, rules = [], [], []
    for i, it in enumerate(batch):
        ob = dict(it["outbound"])
        ob["tag"] = f"out{i}"
        outbounds.append(ob)
        inbounds.append({"tag": f"in{i}", "listen": "127.0.0.1", "port": BASE_PORT + i, "protocol": "http", "settings": {}})
        rules.append({"type": "field", "inboundTag": [f"in{i}"], "outboundTag": f"out{i}"})
    outbounds.append({"protocol": "freedom", "tag": "direct"})
    return {"log": {"loglevel": "none"}, "inbounds": inbounds, "outbounds": outbounds, "routing": {"domainStrategy": "AsIs", "rules": rules}}

def start_xray(batch):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w") as f: json.dump(make_xray_config(batch), f)
    try:
        proc = subprocess.Popen([XRAY_PATH, "run", "-c", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        os.remove(path)
        return None, path

    last_port = BASE_PORT + len(batch) - 1
    deadline = time.time() + 8
    while time.time() < deadline:
        if proc.poll() is not None: return None, path
        try:
            with socket.create_connection(("127.0.0.1", last_port), timeout=0.3): return proc, path
        except OSError: time.sleep(0.1)
    proc.kill()
    return None, path

def ping_via_proxy(port):
    proxies = {"http": f"http://127.0.0.1:{port}", "https": f"http://127.0.0.1:{port}"}
    best = None
    for _ in range(PING_TRIES):
        s = requests.Session()
        s.trust_env = False
        try:
            t = time.perf_counter()
            r = s.get(PING_URL, proxies=proxies, timeout=PING_TIMEOUT, allow_redirects=False)
            ms = int((time.perf_counter() - t) * 1000)
            if r.status_code == 204: best = ms if best is None else min(best, ms)
        except: pass
        finally: s.close()
    return best

def measure_batch(batch):
    if not batch: return []
    proc, path = start_xray(batch)
    if proc is None:
        try: os.remove(path)
        except: pass
        if len(batch) == 1: return [None]
        mid = len(batch) // 2
        return measure_batch(batch[:mid]) + measure_batch(batch[mid:])
    try:
        ports = [BASE_PORT + i for i in range(len(batch))]
        with ThreadPoolExecutor(max_workers=PING_THREADS) as ex:
            return list(ex.map(ping_via_proxy, ports))
    finally:
        proc.terminate()
        try: proc.wait(timeout=5)
        except: proc.kill()
        try: os.remove(path)
        except: pass

def prepare(config):
    parsed = parse_config(config)
    if not parsed: return None
    outbound, host, port, net = parsed

    if any(bad in host.lower() for bad in BLACKLIST): return None

    flags = extract_flags_from_name(get_name(config))
    if not flags: return None

    if net != "kcp" and not check_port(host, port): return None

    names = []
    for f in flags[:2]:
        c_name = get_country_name(f)
        names.append(f"{f} {c_name}" if c_name else f)

    return {"config": config, "outbound": outbound, "name": " -> ".join(names), "flags_key": tuple(names)}

def run():
    if not ensure_xray():
        log_progress("xray не найден и скачать не удалось.")
        return ""

    all_configs = []
    for url in URLS:
        log_progress(f"Загрузка: {url}")
        content = fetch_content(url)
        configs = extract_configs(content)
        log_progress(f"  Найдено конфигов: {len(configs)}")
        all_configs.extend(configs)

    uniq = {}
    for c in all_configs:
        key = c if c.lower().startswith("vmess://") else c.split("#")[0]
        uniq.setdefault(key, c)
    all_configs = list(uniq.values())
    log_progress(f"Всего уникальных конфигов: {len(all_configs)}")

    log_progress("Парсинг и TCP-проверка...")
    with ThreadPoolExecutor(max_workers=100) as executor:
        items = [r for r in executor.map(prepare, all_configs) if r]
    log_progress(f"Прошло TCP-фильтр: {len(items)}")

    log_progress("Замер пинга через xray (gstatic generate_204)...")
    results = []
    for i in range(0, len(items), BATCH_SIZE):
        batch = items[i:i + BATCH_SIZE]
        log_progress(f"Проверяем батч {i // BATCH_SIZE + 1}...")
        pings = measure_batch(batch)
        for it, ping in zip(batch, pings):
            results.append((it, ping))
        ok = sum(1 for p in pings if p is not None)
        log_progress(f"  живых {ok}/{len(batch)}")

    good = sorted(((it, p) for it, p in results if p is not None and p <= MAX_PING_MS), key=lambda x: x[1])
    bad = [(it, None) for it, p in results if p is None or p > MAX_PING_MS]
    all_sorted = good + (bad if KEEP_FAILED else [])

    final = []
    country_counts = {}
    skipped = []
    
    for it, ping in all_sorted:
        if len(final) >= MAX_SERVERS_TOTAL: break
        flags_key = it["flags_key"]
        current_count = country_counts.get(flags_key, 0)
        if current_count >= MAX_SERVERS_PER_COUNTRY:
            skipped.append((it, ping))
            continue
        final.append((it, ping))
        country_counts[flags_key] = current_count + 1

    if len(final) < MAX_SERVERS_TOTAL:
        needed = MAX_SERVERS_TOTAL - len(final)
        final.extend(skipped[:needed])
        final.sort(key=lambda x: x[1])

    lines = []
    for it, ping in final:
        name = f"{it['name']} • {SUB_NAME}"
        try:
            lines.append(rename_config(it["config"], name))
        except Exception:
            continue

    log_progress(f"Готово! Собрано {len(lines)} серверов.")
    return "\n".join(lines)