import os
import shutil
import time
import threading
from datetime import datetime

from utils.logger import setup_logger
from scripts.user_interface import (
    print_banner, 
    get_orbita_path,
    get_instance_count,
    get_race_limit,
    get_run_mode,
    get_fullscreen_choice,
    get_proxy_choice,
    get_start_method,
    InputListener, 
    CYAN, GREEN, RED, RESET, YELLOW
)
from scripts.worker import run_worker
from scripts.workflow import smart_sleep
from scripts.proxy_handler import count_proxies
from scripts.report_handler import ReportSession, BatchStats, DHAKA_TZ

log = setup_logger("Manager")

class RaceController:
    def __init__(self, limit):
        self.limit = limit
        self.count = 0
        self.lock = threading.Lock()

    def try_enter(self):
        with self.lock:
            if self.count < self.limit:
                self.count += 1
                return True, self.count
            else:
                return False, self.count

def main():
    print_banner()
    
    orbita_path = get_orbita_path()
    instance_count = get_instance_count()
    race_limit_count = get_race_limit(instance_count)
    is_fullscreen = get_fullscreen_choice()
    use_proxy = get_proxy_choice()
    start_method_id, target_start_url = get_start_method()
    is_looping = get_run_mode()

    session = ReportSession()
    log.info(f"Session Report initialized at: {session.session_folder}")

    listener = InputListener()
    listener.start()
    
    batch_counter = 1
    
    while True:
        if listener.stop_gracefully: break
        if listener.stop_now: break

        current_instances = instance_count
        if use_proxy:
            proxies_left = count_proxies()
            if proxies_left == 0:
                print(f"{RED}[!] Proxy list depleted. Stopping session.{RESET}")
                log.error("No proxies left.")
                break
            if proxies_left < instance_count:
                log.warning(f"Only {proxies_left} proxies available. Reducing instances from {instance_count} to {proxies_left}.")
                current_instances = proxies_left

        print(f"\n{CYAN}════════ STARTING BATCH {batch_counter} ════════{RESET}")
        
        batch_start_time = datetime.now(DHAKA_TZ)
        current_race_ctrl = RaceController(limit=race_limit_count)
        current_batch_stats = BatchStats(total_instances=current_instances)
        start_barrier = threading.Barrier(current_instances)
        
        log.info(f"Initializing Batch {batch_counter} with {current_instances} instances.")
        
        threads = []
        
        for i in range(1, current_instances + 1):
            t = threading.Thread(
                target=run_worker, 
                args=(
                    i, batch_counter, listener, current_race_ctrl, 
                    is_fullscreen, use_proxy, 
                    start_method_id, 
                    current_batch_stats, start_barrier, 
                    orbita_path, target_start_url
                )
            )
            threads.append(t)
        
        for t in threads:
            if listener.stop_now: break
            t.start()
            time.sleep(0.1) 

        for t in threads:
            t.join()

        batch_end_time = datetime.now(DHAKA_TZ)

        if listener.stop_now:
            print(f"{RED}════════ EMERGENCY STOP COMPLETED ════════{RESET}")
            break 
            
        print(f"{GREEN}════════ BATCH {batch_counter} COMPLETED ════════{RESET}")
        
        row = session.log_batch(batch_counter, current_batch_stats, batch_start_time, batch_end_time)
        
        print(f"\n   {YELLOW}--- BATCH {batch_counter} REPORT ---{RESET}")
        print(f"   Views (Limit Hit) : {row[1]}")
        print(f"   Completed (Full)  : {row[2]}")
        print(f"   Errors            : {row[3]}")
        print(f"   Duration          : {row[4]}")
        if current_batch_stats.error_details:
             print(f"   {RED}Error Details:{RESET}")
             for err in current_batch_stats.error_details:
                 print(f"    - {err}")
        print(f"   {YELLOW}-----------------------{RESET}\n")
        
        if not is_looping:
            log.info("Run Once mode finished.")
            break
        
        if listener.stop_gracefully:
            log.info("Graceful stop requested. Finishing session.")
            break
            
        if use_proxy and count_proxies() == 0:
            log.error("Proxies exhausted for next batch.")
            break

        log.info("Performing inter-batch cleanup check...")
        temp_root = os.path.join(os.getcwd(), "temp-profiles")
        try:
            if os.path.exists(temp_root):
                for item in os.listdir(temp_root):
                    item_path = os.path.join(temp_root, item)
                    try:
                        if os.path.isdir(item_path): shutil.rmtree(item_path)
                        else: os.remove(item_path)
                    except Exception as e:
                        log.warning(f"Cleanup warn: {item} - {e}")
        except Exception as e:
            log.warning(f"Cleanup warning: {e}")

        log.info(f"Preparing for Batch {batch_counter + 1}...")
        batch_counter += 1
        
        if not smart_sleep(3, listener): break

    session.print_session_summary()
    
    temp_root = os.path.join(os.getcwd(), "temp-profiles")
    try:
        if os.path.exists(temp_root):
            shutil.rmtree(temp_root)
    except: pass

if __name__ == "__main__":
    main()