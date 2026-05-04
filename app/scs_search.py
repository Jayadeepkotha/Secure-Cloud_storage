import os
import sys
import json
import requests
from encryption import decrypt_file, derive_keys
from aws_client import download_file
from dotenv import load_dotenv
import hmac
import hashlib
from aws_client import get_s3_client
import botocore
s3 = get_s3_client()
load_dotenv()

# --- CONFIGURATION ---

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

STATE_FILE = "local_hexie_state.json"
EC2_HOSTNAME = os.getenv("EC2_HOSTNAME", "127.0.0.1")
EC2_URL = f"http://{EC2_HOSTNAME}:5000"

def load_json_state(filepath):
    """Loads the latest secret shares (pi) for keywords."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def perform_search(keyword):
    """Generates Trapdoor and performs a full-chain audit for Index and Storage integrity."""
    keyword = keyword.lower().strip()
    print(f"Searching for keyword: '{keyword}'")
    
    kt1, _, kv = derive_keys(keyword) 
    state = load_json_state(STATE_FILE)
    pi = state.get(keyword)

    if not pi:
        print(f" No local state found for '{keyword}'.")
        return []

    try:
        response = requests.post(f"{EC2_URL}/search", json={"kt1": kt1.hex(), "pi": pi}, timeout=10)
        if response.status_code != 200:
            print(" Connection to EC2 failed.")
            return []

        data = response.json()
        results = data.get('results', [])
        final_pi = data.get('final_pi')
        stop_signal = (b'1' * 16).hex()
        
        # Tracking categories for the report
        total_chain_length = len(results)
        mac_failed = []
        missing_s3 = []
        content_mismatch = []
        verified_files = []

        print(f" Verifying {total_chain_length} chain links...")

        for item in results:
            # Layer 1: Index Integrity (Jianding MAC check)
            tag_content = item['c_w'].encode() + item['s3_key'].encode() + item['f_hash'].encode()
            local_v = hmac.new(kv, tag_content, hashlib.sha256).hexdigest()
            
            if local_v != item['v']:
                mac_failed.append(item['original'])
                print(f" [!] MAC FAILURE: {item['original']}")
                continue 

            # Layer 2: Storage Integrity (Existence and Content Hash check)
            try:
                # Use get_object to verify actual content bytes
                resp = s3.get_object(Bucket=BUCKET_NAME, Key=item['s3_key'])
                actual_bytes = resp['Body'].read()
                
                # Compare fingerprints
                if hashlib.sha256(actual_bytes).hexdigest() == item['f_hash']:
                    print(f" [+] Verified: {item['original']}")
                    verified_files.append(item)
                else:
                    content_mismatch.append(item['original'])
                    print(f" [!] CONTENT MISMATCH: {item['original']}")
                    
            except botocore.exceptions.ClientError as e:
                if e.response['Error']['Code'] == "404":
                    missing_s3.append(item['original'])
                    print(f" [!] REMOVED FROM S3: {item['original']}")

        # --- COMPLETE JIANDING VERIFICATION REPORT ---
        print("\n" + "="*40)
        print(" JIANDING SUMMARY")
        print("="*40)
        print(f" Total Chain Length (EC2): {total_chain_length}")
        print(f" Successfully Verified   : {len(verified_files)}")
        print(f" Index (MAC) Failures    : {len(mac_failed)}")
        print(f" Content (Hash) Failures : {len(content_mismatch)}")
        print(f" Missing (S3) Files      : {len(missing_s3)}")
        
        if mac_failed: print(f" -> Tampered Index: {', '.join(mac_failed)}")
        if content_mismatch: print(f" -> Modified Storage: {', '.join(content_mismatch)}")
        if missing_s3: print(f" -> Deleted Storage: {', '.join(missing_s3)}")
        
        if final_pi == stop_signal:
            print("\n [***] Completeness: Verified (Stop signal reached).")
        else:
            print("\n [!!!] Completeness: FAILED (Chain was cut early).")
            return []

        return verified_files

    except Exception as e:
        print(f" Verification process error: {e}")
        return []
    
def decrypt_and_save(selected_item):
    """Downloads from S3 and decrypts using the original filename context."""
    s3_key = selected_item['s3_key']
    original_name = selected_item['original']
    os.makedirs("downloads", exist_ok=True)
    local_enc_path = os.path.join("downloads", s3_key)
    
    if download_file(s3_key, local_enc_path):
        try:
            # Scoped block: Open, read, and close immediately
            with open(local_enc_path, "rb") as f:
                enc_data = f.read()
            
            # Content verification
            downloaded_hash = hashlib.sha256(enc_data).hexdigest()
            if downloaded_hash != selected_item['f_hash']:
                print(" [!!] CRITICAL FAILURE: S3 File content mismatch!")
                if os.path.exists(local_enc_path):
                    os.remove(local_enc_path) # Now safe to delete
                return None
                
            # Decryption
            plain_data = decrypt_file(enc_data, original_name) 
            output_path = os.path.join("downloads", f"RESTORED_{original_name}")
            with open(output_path, "wb") as f_out:
                f_out.write(plain_data)
            
            if os.path.exists(local_enc_path):
                os.remove(local_enc_path) 
            return output_path
        except Exception as e:
            print(f" Error: {e}")
            return None
    return None

def run_search_interface(keyword):
    """Terminal UI for the Hexie search process ."""
    matches = perform_search(keyword) 
    if not matches:
        print(f" No matching records found for: '{keyword}'")
        return
 
    print(f"\n Found {len(matches)} matching file(s) on EC2:")
    for i, item in enumerate(matches):
        # Fix: Access 'original' filename from the EC2 result dictionary[cite: 1]
        print(f"[{i}] {item['original']} (S3 ID: {item['s3_key'][:12]}...)")

    try:
        choice = int(input("\nEnter the file number to download: "))
        selected_item = matches[choice]
        result_path = decrypt_and_save(selected_item)
        if result_path:
            print(f" Success! File restored to: {os.path.abspath(result_path)}")
    except (ValueError, IndexError):
        print(" Invalid selection.")
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scs_search.py <keyword>")
    else:
        run_search_interface(sys.argv[1])