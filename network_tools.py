import socket
import subprocess
import platform
import os
from datetime import datetime

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "network_log.txt")

def init_log():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def write_log(action, target, result):
    init_log()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {action} | {target} | {result}\n")

def ping(host):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    result = subprocess.call(
        ["ping", param, "1", host],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    status = result == 0
    write_log("PING", host, "SUCCESS" if status else "FAILED")
    return status

def ping_latency(host):
    param = "-n" if platform.system().lower() == "windows" else "-c"
    try:
        output = subprocess.check_output(
            ["ping", param, "1", host],
            universal_newlines=True
        )
        for line in output.splitlines():
            if "time=" in line.lower():
                latency = line.split("time=")[-1].split("ms")[0].strip()
                write_log("LATENCY", host, latency)
                return latency
    except:
        return None

def dns_lookup(domain):
    try:
        ip = socket.gethostbyname(domain)
        write_log("DNS", domain, ip)
        return ip
    except:
        write_log("DNS", domain, "FAILED")
        return None

def check_port(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        sock.close()
        status = result == 0
        write_log("PORT", f"{host}:{port}", "OPEN" if status else "CLOSED")
        return status
    except:
        return False
