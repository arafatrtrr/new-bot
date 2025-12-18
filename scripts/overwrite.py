import os
import json
from utils.logger import setup_logger

# Initialize Logger for this module
log = setup_logger("Overwrite")

def override_profile_settings(profile_path, timezone_id, fingerprint_data):
    """
    Surgically modifies the 'gologin' section of the Preferences file 
    to inject Timezone, WebGL Vendor/Renderer, and RAM.
    """
    # 1. Construct Absolute Path
    pref_file = os.path.abspath(os.path.join(profile_path, "Default", "Preferences"))
    
    if not os.path.exists(pref_file):
        log.error(f"Preferences file not found at: {pref_file}")
        return False

    try:
        # 2. READ JSON
        with open(pref_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if "gologin" not in data:
            log.error(f"Start Error: 'gologin' key not found in Preferences.")
            return False

        gologin = data["gologin"]

        # ==========================
        # 1. APPLY TIMEZONE
        # ==========================
        if timezone_id:
            if "timezone" not in gologin: gologin["timezone"] = {}
            gologin["timezone"]["mode"] = "manual"
            gologin["timezone"]["id"] = timezone_id
            log.info(f"SET Timezone  : {timezone_id}")

        # ==========================
        # 2. APPLY FINGERPRINT
        # ==========================
        if fingerprint_data:
            # Vendor
            gologin["vendor"] = fingerprint_data["vendor"]
            # Renderer
            gologin["renderer"] = fingerprint_data["renderer"]
            # RAM (in MB)
            gologin["deviceMemory"] = fingerprint_data["deviceMemory"]
            
            log.info(f"SET Hardware  : {fingerprint_data['vendor']} | {fingerprint_data['renderer']} | {fingerprint_data['deviceMemory']} MB")

        # ==========================
        # 3. WRITE JSON
        # ==========================
        with open(pref_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
            
        return True
    except Exception as e:
        log.error(f"Failed to override profile settings: {e}")
        return False

def verify_settings(profile_path):
    """
    Reads the file back to verify changes on disk.
    Returns a string summary.
    """
    pref_file = os.path.abspath(os.path.join(profile_path, "Default", "Preferences"))
    try:
        with open(pref_file, 'r', encoding='utf-8') as f:
            data = json.load(f).get("gologin", {})
            
            tz = data.get("timezone", {}).get("id", "Unknown")
            rend = data.get("renderer", "Unknown")
            mem = data.get("deviceMemory", "Unknown")
            
            return f"TZ: {tz} | GPU: {rend} | RAM: {mem}"
    except:
        return "Error Reading File"