import os
import sys
import hashlib
import json
import uuid
import re
from PyPDF2 import PdfReader 
from encryption import encrypt_file
from aws_client import upload_file

DF_MAP = "local_df.json"
DI_MAP = "local_di.json"
STATE_MAP = "local_di_state.json" # Added state tracking

def load_json_state(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return json.loads(content) if content else {}
        except:
            return {}
    return {}

def get_clean_keywords(abs_path):
    raw_words = []
    file_name = os.path.basename(abs_path)
    raw_words.extend(re.split(r'[-_.\s]', file_name.lower()))
    
    try:
        if abs_path.endswith('.pdf'):
            reader = PdfReader(abs_path)
            for page in reader.pages:
                text = page.extract_text()
                if text: raw_words.extend(text.lower().split())
    except:
        pass

    # Basic stop words
    stop_words = {'the', 'and', 'for', 'this', 'that', 'with', 'from', 'your', 'will', 'pdf', 'enc'}
    
    # NEW: Coding word filter (skips common syntax/programming terms)
    coding_words = {
        'import', 'from', 'return', 'def', 'class', 'self', 'void', 'public', 
        'private', 'string', 'int', 'float', 'print', 'const', 'true', 'false',
        'null', 'undefined', 'async', 'await', 'function', 'var', 'let', 'typeof'
    }

    useful = set()
    for word in raw_words:
        clean_word = re.sub(r'[^a-z0-9]', '', word)
        
        # Filter Logic
        is_coding = clean_word in coding_words
        if clean_word.isalpha() and len(clean_word) >= 3 and clean_word not in stop_words and not is_coding:
            useful.add(clean_word)
        elif clean_word.isdigit() and len(clean_word) >= 9:
            useful.add(clean_word)
            
    return list(useful)

def run_upload(abs_path):
    if not os.path.exists(abs_path):
        print(f"❌ Error: {abs_path} not found.")
        return

    file_base = os.path.basename(abs_path)
    print(f"🔍 Extracting metadata from: {file_base}")
    keywords = get_clean_keywords(abs_path)

    # Load all three local states
    df = load_json_state(DF_MAP)
    di = load_json_state(DI_MAP)
    state = load_json_state(STATE_MAP)
    
    # Algorithm 2: Generate unique S3 key
    # In a full Hexie implementation, this UUID would be derived from the secret share in state.json
    cloud_id = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()
    s3_key = f"{cloud_id}.enc"

    # Update Forward Index (File -> Keywords)
    df[file_base] = keywords
    
    # Update Inverted Index (Keyword -> Cloud File)
    for kw in keywords:
        if kw not in di: 
            di[kw] = []
            # Initialize a new secret share/state for this new keyword
            state[kw] = {"last_share": hashlib.sha256(os.urandom(16)).hexdigest()}
        
        di[kw].append({"s3_key": s3_key, "original": file_base})

    print(f"🔒 Encrypting locally...")
    with open(abs_path, "rb") as f:
        ciphertext = encrypt_file(f.read(), file_base)

    os.makedirs("cloud_artifacts", exist_ok=True)
    enc_path = os.path.join("cloud_artifacts", s3_key)
    with open(enc_path, "wb") as f:
        f.write(ciphertext)

    print(f"☁️ Uploading to S3: {s3_key}")
    if upload_file(enc_path, s3_key):
        # MANDATORY: Save all three files to persist the state
        with open(DF_MAP, "w", encoding="utf-8") as f: json.dump(df, f, indent=4)
        with open(DI_MAP, "w", encoding="utf-8") as f: json.dump(di, f, indent=4)
        with open(STATE_MAP, "w", encoding="utf-8") as f: json.dump(state, f, indent=4)
        print(f"✅ Success! {len(keywords)} tokens indexed and state updated.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scs_client.py <abs_path>")
    else:
        run_upload(sys.argv[1])