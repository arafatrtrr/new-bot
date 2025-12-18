import os
import threading
import shutil
import zipfile
import socket # <--- Replaces urllib for faster connection check
import requests
import time

# Global lock to prevent two threads grabbing the same line
file_lock = threading.Lock()

PROXY_FILE = os.path.join(os.getcwd(), "proxy", "proxy.txt")

def count_proxies():
    """Returns the number of lines/proxies left in the file."""
    if not os.path.exists(PROXY_FILE):
        return 0
    with open(PROXY_FILE, 'r') as f:
        lines = [line.strip() for line in f if line.strip()]
    return len(lines)

def get_proxy_and_delete():
    """
    Reads the first line of the proxy file, deletes it from the file,
    and returns the proxy string.
    """
    with file_lock:
        if not os.path.exists(PROXY_FILE):
            return None
            
        with open(PROXY_FILE, 'r') as f:
            lines = f.readlines()
            
        lines = [line.strip() for line in lines if line.strip()]
        
        if not lines:
            return None
            
        proxy_data = lines.pop(0)
        
        with open(PROXY_FILE, 'w') as f:
            for line in lines:
                f.write(line + "\n")
                
        return proxy_data

def parse_proxy(proxy_string):
    """
    Parses 'host:port:user:pass' into a dictionary.
    """
    try:
        parts = proxy_string.split(':')
        if len(parts) == 4:
            return {
                'host': parts[0],
                'port': parts[1],
                'user': parts[2],
                'pass': parts[3]
            }
        elif len(parts) == 2:
            return {
                'host': parts[0],
                'port': parts[1],
                'user': None,
                'pass': None
            }
    except:
        pass
    return None

def get_proxy_timezone(proxy_data):
    """
    Connects to an IP API through the proxy to determine its Timezone ID.
    Retries once after 5 seconds if the first attempt fails.
    """
    auth_part = ""
    if proxy_data['user'] and proxy_data['pass']:
        auth_part = f"{proxy_data['user']}:{proxy_data['pass']}@"
    
    proxy_url = f"http://{auth_part}{proxy_data['host']}:{proxy_data['port']}"
    
    proxies = {
        "http": proxy_url,
        "https": proxy_url
    }

    for attempt in range(1, 3):
        try:
            print(f"   > [Attempt {attempt}] Detecting Timezone for {proxy_data['host']}...")
            response = requests.get("http://ip-api.com/json", proxies=proxies, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'timezone' in data:
                    return data['timezone']
        except Exception as e:
            print(f"   > Attempt {attempt} failed: {e}")
        
        if attempt == 1:
            print("   > Waiting 5 seconds before retry...")
            time.sleep(5)
            
    return None

def create_proxy_extension(instance_id, proxy_data):
    """
    Creates a temporary Chrome Extension to handle User/Pass auth.
    """
    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version":"22.0.0"
    }
    """

    background_js = """
    var config = {
            mode: "fixed_servers",
            rules: {
              singleProxy: {
                scheme: "http",
                host: "%s",
                port: parseInt(%s)
              },
              bypassList: ["localhost"]
            }
          };

    chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

    function callbackFn(details) {
        return {
            authCredentials: {
                username: "%s",
                password: "%s"
            }
        };
    }

    chrome.webRequest.onAuthRequired.addListener(
                callbackFn,
                {urls: ["<all_urls>"]},
                ['blocking']
    );
    """ % (proxy_data['host'], proxy_data['port'], proxy_data['user'], proxy_data['pass'])

    temp_dir = os.path.join(os.getcwd(), "temp-profiles")
    if not os.path.exists(temp_dir): os.makedirs(temp_dir)
    
    plugin_file = os.path.join(temp_dir, f"proxy_auth_plugin_{instance_id}.zip")

    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)

    return plugin_file

def check_internet_connection():
    """
    Checks if the local machine has internet access by attempting 
    a socket connection to Google DNS (8.8.8.8) on port 53.
    """
    try:
        # 8.8.8.8 is Google's DNS, 53 is the standard DNS port.
        # This is extremely lightweight compared to an HTTP request.
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False