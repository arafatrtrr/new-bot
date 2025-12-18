import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ==============================
# CONFIGURATION
# ==============================
PAGE_LOAD_WAIT = 10 
LANDING_PAGE_WAIT = 5 

def smart_sleep(seconds, listener_obj):
    end_time = time.time() + seconds
    while time.time() < end_time:
        if listener_obj.stop_now: return False 
        time.sleep(0.5)
    return True

def get_current_domain(driver):
    try: return driver.current_url.split('/')[2]
    except: return "unknown"

def find_and_switch_iframe(driver, wait, by_method, selector, log, worker_tag):
    log.info(f"{worker_tag} Finding Iframe ({selector})...")
    try:
        iframe = wait.until(EC.presence_of_element_located((by_method, selector)))
        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", iframe)
        time.sleep(1)
        driver.switch_to.frame(iframe)
        log.info(f"{worker_tag} -> Switched successfully.")
        return True
    except Exception as e:
        log.warning(f"{worker_tag} -> Could not switch/find iframe: {e}")
        return False

def switch_to_new_tab(driver, old_handles, wait_obj, log, worker_tag):
    log.info(f"{worker_tag} Waiting for new tab...")
    try:
        wait_obj.until(EC.number_of_windows_to_be(len(old_handles) + 1))
        new_window = [w for w in driver.window_handles if w not in old_handles][0]
        driver.switch_to.window(new_window)
        log.info(f"{worker_tag} -> Switched to new tab.")
        return True
    except Exception as e:
        log.error(f"{worker_tag} -> Tab switch failed: {e}")
        return False

def execute_entry_click(driver, wait, log, worker_tag, start_method, listener_obj):
    handles_before = driver.window_handles
    
    if start_method == 1:
        if find_and_switch_iframe(driver, wait, By.XPATH, "//iframe[contains(@src, 'facebook')]", log, worker_tag):
            log.info(f"{worker_tag} Finding Titan Link...")
            try:
                link = wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, "titansearch.top")))
                log.info(f"{worker_tag} -> Clicking...")
                link.click()
                time.sleep(1)
                driver.switch_to.default_content()
                return switch_to_new_tab(driver, handles_before, wait, log, worker_tag)
            except Exception as e:
                log.error(f"{worker_tag} -> Titan Link interaction failed: {e}")
                return False
        return False

    elif start_method == 2:
        log.info(f"{worker_tag} Finding Xaria Links...")
        try:
            xpath = "//a[contains(@href, 'xaria.trckswrm.com')]"
            links = driver.find_elements(By.XPATH, xpath)
            count = len(links)
            log.info(f"{worker_tag} -> Found {count} Xaria links.")
            
            if count > 0:
                target = random.choice(links)
                log.info(f"{worker_tag} Clicking link...")
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", target)
                time.sleep(1)
                
                try: target.click()
                except: driver.execute_script("arguments[0].click();", target)
                
                time.sleep(1)
                try:
                    if len(driver.window_handles) > len(handles_before):
                        return switch_to_new_tab(driver, handles_before, wait, log, worker_tag)
                    else:
                        log.info(f"{worker_tag} Link opened in same tab.")
                        return True
                except: return True
            else:
                log.error(f"{worker_tag} -> No links found.")
                return False
        except Exception as e:
            log.error(f"{worker_tag} -> Method 2 Error: {e}")
            return False

def run_automation_task(driver, log, worker_tag, listener_obj, race_ctrl, start_method, batch_stats, instance_id, target_start_url):
    
    if listener_obj.stop_now: raise InterruptedError("Force Stop")
    wait = WebDriverWait(driver, 15)
    inner_wait = WebDriverWait(driver, 5)
    is_counted_as_view = False 

    # STEP 1
    page_name = "Entry Page"
    url = target_start_url
    log.info(f"{worker_tag} [Step 1] Navigating to {url}...")
    try: driver.get(url)
    except: return

    log.info(f"{worker_tag} Waiting {PAGE_LOAD_WAIT}s...")
    if not smart_sleep(PAGE_LOAD_WAIT, listener_obj): raise InterruptedError("Stop")

    if not execute_entry_click(driver, wait, log, worker_tag, start_method, listener_obj):
        batch_stats.register_error(instance_id, "Entry Click Failed", page_name, get_current_domain(driver), is_counted_as_view)
        log.error(f"{worker_tag} Step 1 Failed.")
        return

    # STEP 2
    log.info(f"{worker_tag} Waiting {PAGE_LOAD_WAIT}s for Pre-Visit...")
    if not smart_sleep(PAGE_LOAD_WAIT, listener_obj): raise InterruptedError("Stop")
    
    page_name = "Pre-Visit Page"
    step2_success = False
    
    try:
        for attempt in range(1, 4):
            log.info(f"{worker_tag} [Page: {page_name}] Attempt {attempt}...")
            
            try:
                if "waterheaterrepairandreplacementpro.cyou" in driver.current_url:
                    log.warning(f"{worker_tag} \033[93m[BAD DOMAIN]\033[0m Backtracking...")
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        if execute_entry_click(driver, wait, log, worker_tag, start_method, listener_obj):
                             smart_sleep(PAGE_LOAD_WAIT, listener_obj)
                             continue
                    raise Exception("Backtrack failed")
            except Exception as e:
                if "Backtrack" in str(e): raise e

            driver.switch_to.default_content()
            iframe_found = False
            
            if find_and_switch_iframe(driver, wait, By.ID, "master-1", log, worker_tag):
                iframe_found = True
            else:
                log.warning(f"{worker_tag} [{page_name}] Iframe NOT found.")

            if not iframe_found:
                if attempt == 1:
                    log.warning(f"{worker_tag} Reloading...")
                    driver.refresh()
                    smart_sleep(5, listener_obj)
                    continue 
                elif attempt == 2:
                    log.warning(f"{worker_tag} \033[93m[BACKTRACKING]\033[0m Returning...")
                    if len(driver.window_handles) > 1:
                        driver.close()
                        driver.switch_to.window(driver.window_handles[0])
                        if execute_entry_click(driver, wait, log, worker_tag, start_method, listener_obj):
                             smart_sleep(PAGE_LOAD_WAIT, listener_obj)
                             continue
                        else: raise Exception("Backtrack failed")
                    else: raise Exception("Cannot backtrack")
                else: raise Exception("Iframe missing after backtrack")

            log.info(f"{worker_tag} Finding links in iframe...")
            try:
                links = inner_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".i_.a.si144")))
                if len(links) > 0:
                    target = random.choice(links)
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", target)
                    time.sleep(1)
                    driver.execute_script("arguments[0].click();", target)
                    log.info(f"{worker_tag} -> Clicked.")
                    step2_success = True
                    break 
                else: raise Exception("0 links found")
            except Exception as e:
                log.warning(f"{worker_tag} Link error: {e}")
                driver.switch_to.default_content()
                if attempt < 3:
                    driver.refresh()
                    smart_sleep(5, listener_obj)
                else: raise Exception("No links after retries")

        if not step2_success: raise Exception("Step 2 Failed")

    except Exception as e:
        batch_stats.register_error(instance_id, f"Step 2: {e}", page_name, get_current_domain(driver), is_counted_as_view)
        return

    log.info(f"{worker_tag} Waiting {PAGE_LOAD_WAIT}s...")
    if not smart_sleep(PAGE_LOAD_WAIT, listener_obj): raise InterruptedError("Stop")

    # STEP 3
    page_name = "Visit Website Page"
    batch_stats.register_view_reached()
    is_counted_as_view = True
    step3_success = False
    
    try:
        for attempt in range(1, 3):
            log.info(f"{worker_tag} [Page: {page_name}] Attempt {attempt}...")
            driver.switch_to.default_content()

            if find_and_switch_iframe(driver, wait, By.ID, "master-1", log, worker_tag):
                try:
                    xpath = "//span[@class='m_ n_ si22 span' and text()='Visit Website']"
                    buttons = inner_wait.until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
                    log.info(f"{worker_tag} -> Found {len(buttons)} buttons.")
                    
                    log.info(f"{worker_tag} Requesting Permission...")
                    allowed, rank = race_ctrl.try_enter()
                    if not allowed:
                        log.info(f"{worker_tag} \033[96m[LIMIT REACHED]\033[0m Stopping task.")
                        return 
                    log.info(f"{worker_tag} \033[92m[GO]\033[0m Permission Granted.")
                    
                    target = random.choice(buttons)
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", target)
                    time.sleep(1)
                    
                    handles_before = driver.window_handles
                    driver.execute_script("arguments[0].click();", target)
                    log.info(f"{worker_tag} -> Clicked.")
                    
                    time.sleep(1)
                    driver.switch_to.default_content()
                    
                    if switch_to_new_tab(driver, handles_before, wait, log, worker_tag):
                         log.info(f"{worker_tag} Switched to Sponsored flow.")
                         batch_stats.register_click_success()
                         step3_success = True
                         break
                    else: 
                         log.error(f"{worker_tag} -> Click did not open new tab.")
                         return

                except Exception as e:
                    log.warning(f"{worker_tag} -> Button error: {e}")
                    driver.switch_to.default_content()
                    if attempt == 1:
                        driver.refresh()
                        smart_sleep(5, listener_obj)
                    else: raise Exception("Buttons missing")
            else:
                if attempt == 1:
                    driver.refresh()
                    smart_sleep(5, listener_obj)
                else: raise Exception("Iframe missing")

        if not step3_success: raise Exception("Step 3 Failed")

    except Exception as e:
        batch_stats.register_error(instance_id, f"Step 3: {e}", page_name, get_current_domain(driver), is_counted_as_view)
        return

    log.info(f"{worker_tag} Waiting {PAGE_LOAD_WAIT}s...")
    if not smart_sleep(PAGE_LOAD_WAIT, listener_obj): raise InterruptedError("Stop")

    # STEP 4
    page_name = "Sponsored Flow"
    try:
        sponsored_depth = 0
        while sponsored_depth < 10:
            driver.switch_to.default_content()
            has_m1 = len(driver.find_elements(By.ID, "master-1")) > 0
            has_m2 = len(driver.find_elements(By.ID, "master-2")) > 0
            
            if not has_m1 and not has_m2:
                log.info(f"{worker_tag} \033[96m[Landing Page]\033[0m End of chain.")
                smart_sleep(LANDING_PAGE_WAIT, listener_obj)
                break
            else:
                sponsored_depth += 1
                target_id = "master-1" if has_m1 else "master-2"
                log.info(f"{worker_tag} [Sponsored #{sponsored_depth}] Target: {target_id}")
                
                if find_and_switch_iframe(driver, wait, By.ID, target_id, log, worker_tag):
                    try:
                        css = ".p_.si27.a, .i_.a.si21, .p_.si65.a, .i_.a.si144"
                        links = inner_wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, css)))
                        
                        link = random.choice(links)
                        target_attr = link.get_attribute("target")
                        is_new_tab = target_attr and "_blank" in target_attr
                        
                        log.info(f"{worker_tag} -> Target: '{target_attr}'. Clicking...")
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", link)
                        time.sleep(1)
                        handles_before = driver.window_handles
                        driver.execute_script("arguments[0].click();", link)
                        
                        time.sleep(1)
                        driver.switch_to.default_content()
                        
                        if is_new_tab:
                            if switch_to_new_tab(driver, handles_before, wait, log, worker_tag):
                                smart_sleep(PAGE_LOAD_WAIT, listener_obj)
                            else: break
                        else:
                            smart_sleep(PAGE_LOAD_WAIT, listener_obj)

                    except Exception as e:
                        log.warning(f"{worker_tag} Treating as Landing. Error: {e}")
                        smart_sleep(LANDING_PAGE_WAIT, listener_obj)
                        break
                else: break
        
        log.info(f"{worker_tag} Workflow executed successfully.")
        batch_stats.register_completion()

    except Exception as e:
        batch_stats.register_error(instance_id, f"Step 4 Failed: {e}", page_name, get_current_domain(driver), is_counted_as_view)