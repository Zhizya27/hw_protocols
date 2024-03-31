
import subprocess
import re
import requests
from prettytable import PrettyTable

def run_tracert(ip):
    try:
        result = subprocess.run(["tracert", "-4", "-d", ip], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError:
        print("Error: Не удалось выполнить команду трассировки маршрута.")
        return ""

def extract_ip_addresses(stdout):
    reg = re.compile("\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}\\.\\d{1,3}")
    ip_addresses = reg.findall(stdout)[1:]
    return ip_addresses

def get_info(ip_address):
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}?fields=27137")
        response.raise_for_status()
        info = response.json()
        if info["status"] == "success":
            as_info = info.get("as", "Nil").split()[0]
            return as_info
        else:
            return "local"
    except Exception as e:
        return "error"

def tracert(ip):
    stdout = run_tracert(ip)
    if not stdout:
        return

    ip_addresses = extract_ip_addresses(stdout)

    table = PrettyTable(["HOP", "IP", "AS"])
    for i, ip_address in enumerate(ip_addresses, start=1):
        as_info = get_info(ip_address)
        table.add_row([i, ip_address, as_info])

    print(table)

def main():
    target = input("Введите IP-адрес или доменное имя: ")
    tracert(target)

if __name__ == "__main__":
    main()
