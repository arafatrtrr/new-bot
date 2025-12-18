import os
import threading
import sys
import json
from utils.logger import setup_logger

log = setup_logger("UI")

# COLORS
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_banner():
    os.system('cls' if os.name == 'nt' else 'clear') 
    banner = f"""
{CYAN}
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   {BOLD}WEB AUTOMATION FRAMEWORK v2.2{RESET}{CYAN}                              ║
║   {YELLOW}Advanced Fingerprinting & Logic{RESET}{CYAN}                           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
{RESET}"""
    print(banner)

def get_orbita_path():
    json_path = os.path.join(os.getcwd(), "options", "path.json")
    default_path = r"C:\Users\trr\.gologin\browser\orbita-browser-134\chrome.exe"

    if not os.path.exists(json_path):
        log.warning(f"Path config not found at {json_path}. Using default.")
        return default_path

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list) or not data:
            log.warning("Path config is empty/invalid. Using default.")
            return default_path

        print(f"\n{GREEN}[?] Select Orbita Browser Path:{RESET}")
        for idx, item in enumerate(data, 1):
            name = item.get("name", "Unknown")
            val = item.get("value", "Unknown Path")
            print(f"   {YELLOW}{idx}.{RESET} {BOLD}{name}{RESET}")

        try:
            choice = input(f"{BOLD}   >>> {RESET}").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(data):
                selected = data[idx].get("value", default_path)
                selected_name = data[idx].get("name", "Unknown")
                print(f"{CYAN}   [+] Selected: {selected_name}{RESET}")
                return selected
            else:
                print(f"{RED}   [!] Invalid selection. Using Option 1.{RESET}")
                return data[0].get("value", default_path)
        except ValueError:
            print(f"{RED}   [!] Invalid input. Using Option 1.{RESET}")
            return data[0].get("value", default_path)

    except Exception as e:
        log.error(f"Error reading path.json: {e}")
        return default_path

def get_custom_url():
    json_path = os.path.join(os.getcwd(), "options", "entry_urls.json")
    default_url = "https://tinyurl.com/Akash-X-02"

    if not os.path.exists(json_path):
        log.warning(f"URL config not found. Using default.")
        return default_url

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\n{GREEN}[?] Select the TinyURL Entry Point:{RESET}")
        for idx, item in enumerate(data, 1):
            name = item.get("name", "Link")
            val = item.get("value", "Unknown URL")
            print(f"   {YELLOW}{idx}.{RESET} {BOLD}{name:<10}{RESET} ->  {val}")

        choice = input(f"{BOLD}   >>> {RESET}").strip()
        idx = int(choice) - 1
        if 0 <= idx < len(data):
            selected = data[idx].get("value", default_url)
            selected_name = data[idx].get("name", "Unknown")
            print(f"{CYAN}   [+] Selected: {selected_name} ({selected}){RESET}")
            return selected
        return data[0].get("value", default_url)
    except:
        return default_url

def get_start_method():
    print(f"\n{GREEN}[?] Select Starting Entry Point:{RESET}")
    print(f"   {YELLOW}1.{RESET} LatestCarNews (Facebook Iframe)")
    print(f"   {YELLOW}2.{RESET} Custom TinyURL (Select from list)")
    
    choice = input(f"{BOLD}   >>> {RESET}").strip()
    
    if choice == '2':
        selected_url = get_custom_url()
        print(f"{CYAN}   [+] Method Selected: Custom TinyURL{RESET}")
        return 2, selected_url
    
    print(f"{CYAN}   [+] Method Selected: Facebook Iframe{RESET}")
    return 1, "https://latestcarnews.online/e-1225-seaid/"

def get_instance_count():
    print(f"\n{GREEN}[?] How many profile instances do you want to run at once?{RESET}")
    try:
        val = int(input(f"{BOLD}   >>> {RESET}"))
        final_val = max(1, val)
    except ValueError:
        final_val = 1
    print(f"{CYAN}   [+] Selected: {final_val} Instance(s){RESET}")
    return final_val

def get_race_limit(total_instances):
    print(f"\n{GREEN}[?] Set the Checkpoint Limit (How many profiles are allowed to finish?){RESET}")
    print(f"    {YELLOW}(You selected {total_instances} total instances){RESET}")
    try:
        val = int(input(f"{BOLD}   >>> {RESET}"))
        if val < 0: final_val = 0
        else: final_val = val
    except ValueError:
        final_val = total_instances 
    print(f"{CYAN}   [+] Limit Set: {final_val} Profiles{RESET}")
    return final_val

def get_fullscreen_choice():
    print(f"\n{GREEN}[?] Start browsers in Full Screen mode? (y/n){RESET}")
    choice = input(f"{BOLD}   >>> {RESET}").strip().lower()
    if choice in ['1', 'y', 'yes']:
        print(f"{CYAN}   [+] Full Screen: ENABLED{RESET}")
        return True
    print(f"{CYAN}   [+] Full Screen: DISABLED{RESET}")
    return False

def get_proxy_choice():
    print(f"\n{GREEN}[?] Use Proxies from ./proxy/proxy.txt? (y/n){RESET}")
    choice = input(f"{BOLD}   >>> {RESET}").strip().lower()
    if choice in ['1', 'y', 'yes']:
        print(f"{CYAN}   [+] Proxies: ENABLED{RESET}")
        return True
    print(f"{CYAN}   [+] Proxies: DISABLED (Direct Connection){RESET}")
    return False

def get_run_mode():
    print(f"\n{GREEN}[?] Select Execution Mode:{RESET}")
    print(f"   {YELLOW}1.{RESET} Run Once")
    print(f"   {YELLOW}2.{RESET} Loop Indefinitely")
    choice = input(f"{BOLD}   >>> {RESET}").strip().lower()
    if choice in ['2', 'loop']:
        print(f"{CYAN}   [+] Mode: LOOPING{RESET}")
        return True 
    print(f"{CYAN}   [+] Mode: RUN ONCE{RESET}")
    return False

class InputListener:
    def __init__(self):
        self.stop_gracefully = False 
        self.stop_now = False        
        self.thread = threading.Thread(target=self._listen, daemon=True)

    def start(self):
        self.thread.start()
        print(f"\n{YELLOW}[!] Command Listener Active. Type '{BOLD}stop{RESET}{YELLOW}' or '{BOLD}stop -n{RESET}{YELLOW}' anytime.{RESET}")

    def _listen(self):
        while not self.stop_now and not self.stop_gracefully:
            try:
                cmd = sys.stdin.readline().strip().lower()
                if cmd == "stop -n":
                    self.stop_now = True
                    log.warning("COMMAND RECEIVED: IMMEDIATE STOP (stop -n)")
                    print(f"{RED}[!] Initiating Emergency Cleanup...{RESET}")
                    break
                elif cmd == "stop":
                    self.stop_gracefully = True
                    log.warning("COMMAND RECEIVED: STOP GRACEFULLY")
                    print(f"{YELLOW}[!] Will stop after current batch finishes.{RESET}")
                    break
            except: break