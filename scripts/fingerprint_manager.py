import os
import json
import random

# RAM Options in GB
# We will convert these to MB (x 1024)
RAM_GB_OPTIONS = [4, 6, 8, 10, 12, 16, 32, 64]

def get_random_fingerprint():
    """
    Reads the windows_fingerprint.json and generates a random
    hardware configuration (Vendor, Renderer, RAM in MB).
    """
    json_path = os.path.join(os.getcwd(), "fingerprints", "windows_fingerprint.json")
    
    if not os.path.exists(json_path):
        print(f"[!] Error: Fingerprint file not found at {json_path}")
        return None

    try:
        # 1. Load GPU Data
        with open(json_path, 'r') as f:
            gpu_list = json.load(f)

        # 2. Pick Random Vendor Object
        selected_gpu_group = random.choice(gpu_list)
        vendor = selected_gpu_group["vendor"]
        
        # 3. Pick Random Renderer from that Vendor
        renderer = random.choice(selected_gpu_group["renderers"])

        # 4. Pick Random RAM and convert to MB
        # Prompt asked for exact number like 8192 (8 * 1024)
        ram_gb = random.choice(RAM_GB_OPTIONS)
        ram_mb = ram_gb * 1024

        return {
            "vendor": vendor,
            "renderer": renderer,
            "deviceMemory": ram_mb
        }

    except Exception as e:
        print(f"[!] Error generating fingerprint: {e}")
        return None