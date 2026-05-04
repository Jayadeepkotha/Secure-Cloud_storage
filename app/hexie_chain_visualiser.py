import json
import hashlib
import hmac
import os
from encryption import derive_keys

# Paths to your files
STATE_FILE = "local_hexie_state.json"
CLOUD_FILE = "cloud_index.json"

def xor_bytes(b1, b2):
    return bytes(a ^ b for a, b in zip(b1, b2))

def load_safe_json(filepath):
    """Prevents JSONDecodeError by checking file existence and size."""
    if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f" Error: {filepath} is corrupted.")
    return None

def visualize_chain(keyword):
    # 1. Load Data with safety checks
    local_state = load_safe_json(STATE_FILE)
    cloud_index = load_safe_json(CLOUD_FILE)

    if local_state is None or cloud_index is None:
        print(" Error: State or Index files are missing or empty. Upload files first!")
        return

    # 2. Setup Keyword Context
    keyword = keyword.lower().strip()
    if keyword not in local_state:
        print(f" Keyword '{keyword}' not found in local state.")
        return

    # Derive keys (kt1 for unmasking, kv for Jianding MAC)
    kt1, _, kv = derive_keys(keyword)
    current_pi_hex = local_state[keyword]
    stop_signal_hex = (b'1' * 16).hex()
    
    print(f"\n{'='*60}")
    print(f"  JIANDING CHAIN VISUALIZER: '{keyword}'")
    print(f"{'='*60}")
    print(f"Start Trapdoor (π): {current_pi_hex}")
    print(f"Stop Signal (1^λ):  {stop_signal_hex}")
    print(f"{'-'*60}\n")

    link_count = 0
    mac_failures = 0
    current_pi = bytes.fromhex(current_pi_hex)

    while True:
        link_count += 1
        # Calculate the Address (c_w)
        c_w = hashlib.sha256(current_pi).hexdigest()
        
        print(f"LINK #{link_count}")
        print(f"   Address (c_w): {c_w}")

        if c_w not in cloud_index:
            print(f"    BREAK: Address not found in cloud index!")
            break
        
        entry = cloud_index[c_w]
        c_a = bytes.fromhex(entry['c_a'])
        s3_key = entry['c_id']
        original = entry['original']
        v_stored = entry['v']
        f_hash = entry.get('f_hash', '') # Retrieve the file hash

        # 3. Updated Integrity Check (Jianding MAC includes f_hash)[cite: 1]
        tag_content = c_w.encode() + s3_key.encode() + f_hash.encode()
        v_calculated = hmac.new(kv, tag_content, hashlib.sha256).hexdigest()
        
        if v_calculated == v_stored:
            integrity = "  OK"
        else:
            integrity = "  TAMPERED (MAC Mismatch)"
            mac_failures += 1

        # 4. Unmask the pointer (c_a) to find the random string (r)[cite: 1]
        mask = hashlib.sha256(kt1 + current_pi).digest()[:16]
        r = xor_bytes(c_a, mask)
        
        print(f"   File: {original}")
        print(f"   S3 Key: {s3_key[:15]}...")
        print(f"   Integrity: {integrity}")
        print(f"   Unmasked r: {r.hex()}")

        # 5. Calculate next pi (Walking backward through the XOR chain)[cite: 1]
        current_pi = xor_bytes(current_pi, r)
        next_pi_hex = current_pi.hex()
        
        print(f"   Next π:     {next_pi_hex}")

        if next_pi_hex == stop_signal_hex:
            print(f"\n [***] REACHED STOP SIGNAL! Completeness Verified.")
            break
        
        print(f"   {'↓':^30}")

    print(f"\n{'='*60}")
    print(f"AUDIT SUMMARY")
    print(f"Total Chain Length: {link_count}")
    print(f"Integrity Failures: {mac_failures}")
    print(f"{'='*60}")

if __name__ == "__main__":
    kw = input("Enter keyword to visualize: ").strip()
    visualize_chain(kw)