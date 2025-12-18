import os
import shutil
import time
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from utils.logger import setup_logger
from scripts.workflow import run_automation_task
from scripts.proxy_handler import (
    get_proxy_and_delete, parse_proxy, create_proxy_extension, get_proxy_timezone
)
from scripts.fingerprint_manager import get_random_fingerprint
from scripts.overwrite import override_profile_settings, verify_settings

log = setup_logger("Worker")

def run_worker(instance_id, batch_id, listener_obj, race_ctrl, is_fullscreen, use_proxy, start_method, batch_stats, barrier, orbita_path, target_start_url):
    worker_tag = f"[Batch-{batch_id}][Inst-{instance_id}]"
    
    if listener_obj.stop_now: return

    base_dir = os.getcwd()
    original_profile_path = os.path.join(base_dir, r"orignal-gologin-profiles\windows")
    temp_folder_path = os.path.join(base_dir, r"temp-profiles")
    temp_profile_path = os.path.join(temp_folder_path, f"profile{instance_id}")
    
    orbita_binary_path = orbita_path
    chromedriver_path = r"C:\chromedriver.exe"

    max_proxy_attempts = 3
    attempt_counter = 0
    setup_success = False
    current_proxy_extension = None
    driver = None

    try:
        while attempt_counter < max_proxy_attempts:
            attempt_counter += 1
            
            if os.path.exists(temp_profile_path):
                try: shutil.rmtree(temp_profile_path)
                except: pass
            try:
                shutil.copytree(original_profile_path, temp_profile_path)
            except Exception as e:
                log.error(f"{worker_tag} Copy Failed: {e}")
                batch_stats.register_error(instance_id, f"Copy Failed: {e}", "Setup", "Local", False)
                return 

            chrome_options = Options()
            chrome_options.binary_location = orbita_binary_path
            chrome_options.add_argument(f"--user-data-dir={os.path.abspath(temp_profile_path)}")
            chrome_options.add_argument("--no-first-run")
            chrome_options.add_argument("--no-service-autorun")
            chrome_options.add_argument("--password-store=basic")
            if is_fullscreen: chrome_options.add_argument("--start-maximized")

            proxy_str = "Direct"
            timezone_to_set = None
            fingerprint_data = get_random_fingerprint()

            if use_proxy:
                raw_proxy = get_proxy_and_delete()
                if not raw_proxy:
                    log.error(f"{worker_tag} No proxies left! Stopping.")
                    batch_stats.register_error(instance_id, "No Proxies", "Setup", "Local", False)
                    return 

                proxy_data = parse_proxy(raw_proxy)
                if proxy_data:
                    proxy_str = f"{proxy_data['host']}:{proxy_data['port']}"
                    log.info(f"{worker_tag} Configured Proxy: {proxy_str}")
                    
                    timezone_to_set = get_proxy_timezone(proxy_data)
                    
                    if timezone_to_set:
                        log.info(f"{worker_tag} Proxy Alive. TZ: {timezone_to_set}")
                    else:
                        log.warning(f"{worker_tag} TZ Detection failed twice. Proxy assumed dead. Retrying...")
                        continue 

                    if proxy_data['user'] and proxy_data['pass']:
                        current_proxy_extension = create_proxy_extension(instance_id, proxy_data)
                        chrome_options.add_extension(current_proxy_extension)
                    else:
                        chrome_options.add_argument(f"--proxy-server=http://{proxy_data['host']}:{proxy_data['port']}")
                else:
                    log.error(f"{worker_tag} Invalid proxy format. Skipping.")
                    continue

            if override_profile_settings(temp_profile_path, timezone_to_set, fingerprint_data):
                disk_status = verify_settings(temp_profile_path)
                log.info(f"{worker_tag} \033[92m[DISK VERIFY]\033[0m {disk_status}")
            else:
                log.error(f"{worker_tag} Failed to inject settings.")
                batch_stats.register_error(instance_id, "Settings Injection Failed", "Setup", "Local", False)
                return

            setup_success = True
            break 

        if setup_success:
            log.info(f"{worker_tag} Setup Complete. Waiting for batch sync...")
            try:
                barrier.wait(timeout=60)
            except threading.BrokenBarrierError:
                log.warning(f"{worker_tag} Barrier broken. Proceeding...")
            except Exception as e:
                log.warning(f"{worker_tag} Barrier error: {e}")

            time.sleep(instance_id * 0.3)

            service = Service(executable_path=chromedriver_path)
            try:
                log.info(f"{worker_tag} Launching Browser...")
                driver = webdriver.Chrome(service=service, options=chrome_options)
                
                run_automation_task(driver, log, worker_tag, listener_obj, race_ctrl, start_method, batch_stats, instance_id, target_start_url)
                
            except Exception as e:
                log.error(f"{worker_tag} Runtime Error: {e}")
                batch_stats.register_error(instance_id, f"Runtime Error: {e}", "Browser Launch", "Local", False)
        
        else:
            log.error(f"{worker_tag} Failed to setup after {max_proxy_attempts} attempts.")
            batch_stats.register_error(instance_id, "Max Proxy Retries Exceeded", "Setup", "Local", False)

    finally:
        if driver:
            try: driver.quit()
            except: pass
        
        if current_proxy_extension and os.path.exists(current_proxy_extension):
            try: os.remove(current_proxy_extension)
            except: pass

        if not listener_obj.stop_now:
            time.sleep(2) 
        
        try:
            if os.path.exists(temp_profile_path):
                shutil.rmtree(temp_profile_path)
        except: pass