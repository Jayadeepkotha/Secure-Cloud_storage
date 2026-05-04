import hashlib
import hmac
from encryption import derive_keys

def inspect_trapdoor(keyword, pi_hex):
    # 1. Convert input pi from hex to bytes
    pi = bytes.fromhex(pi_hex)
    
    # 2. Derive the search key (kt1) for this keyword
    kt1, _, _ = derive_keys(keyword)
    
    # 3. Calculate the Address (c_w)
    # This should match the 'key' in your cloud_index.json
    c_w = hashlib.sha256(pi).hexdigest()
    
    # 4. Calculate the Mask used for c_a
    # c_a = r XOR mask. To find 'r' (the link to the next pi), 
    # you would XOR the c_a in your JSON with this value.
    mask = hashlib.sha256(kt1 + pi).digest()[:16]
    
    print(f"\n--- Hexie Protocol Inspector ---")
    print(f"Keyword:   {keyword}")
    print(f"Current π: {pi_hex}")
    print(f"---------------------------------")
    print(f"EXPECTED Address (c_w):")
    print(f" {c_w}")
    print(f"\nEXPECTED Mask (to decrypt c_a):")
    print(f" {mask.hex()}")
    print(f"---------------------------------")
    print(f"Manual check: In your EC2 cloud_index.json, find the entry")
    print(f"with the address above. Take its 'c_a' and XOR it with")
    print(f"the mask above to find the 'r' for the next link.")

if __name__ == "__main__":
    kw = input("Enter keyword (e.g., venu): ").strip()
    p = input("Enter π from local_state.json (hex): ").strip()
    inspect_trapdoor(kw, p)