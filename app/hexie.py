import hashlib
import os
import json

STATE_FILE = "local_di_state.json"

def load_di():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_di(di):
    with open(STATE_FILE, "w") as f:
        json.dump(di, f)

def get_trapdoor(keyword):
    """Algorithm 4: Trapdoor Generation[cite: 342]."""
    di = load_di()
    pi = di.get(keyword)
    if not pi:
        return None
    
    from encryption import derive_keys
    k_t1, _ = derive_keys(keyword)
    # Returns (kt1, pi) [cite: 342]
    return k_t1.hex(), pi