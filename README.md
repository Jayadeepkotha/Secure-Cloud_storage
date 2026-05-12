# Secure Cloud Storage

A research-grade implementation of a **Verifiable Dynamic Searchable Symmetric Encryption (DSSE)** system built on AWS. This version implements the **Hexie XOR-chain indexing** protocol for encrypted keyword search, the **Jianding dual-layer verification** scheme for proving storage and index integrity, and a **Hierarchical Tree-based Verifiable DSSE (HTV-DSSE)** access control model using threshold secret sharing.

---

## Overview

Traditional cloud storage assumes the storage provider is trusted with file contents and metadata. This system eliminates that assumption:

- Files are **encrypted client-side** (AES-GCM) before leaving the machine.
- Only **ciphertext blobs** reach Amazon S3.
- A structured **encrypted inverted index** lives on an EC2 server; the cloud server never learns the keyword or file contents.
- Every search retrieval is accompanied by a **cryptographic proof** (Jianding) that the index and stored file have not been tampered with or silently deleted.

---

## Core Cryptographic Concepts

### 1. Key Derivation (Algorithm 1)
Three independent keys are derived per-keyword using HMAC-SHA256 over a local master key:
- **`kt1`** — search/trapdoor key used for XOR chain traversal
- **`k2`** — file encryption key (AES-GCM)
- **`kv`** — verification key used to generate and validate Jianding MAC tags

### 2. Hexie XOR-Chain Indexing (Algorithms 2 & 3)
Each keyword maps to a **linked chain of encrypted index entries** stored on EC2. The chain is built during upload:

```
For each keyword kw:
  π_new = π_prev XOR r          (where r = random nonce)
  c_w   = SHA256(π_new)         (encrypted index pointer / bucket key)
  mask  = SHA256(kt1 || π_new)
  c_a   = r XOR mask            (encrypted address payload)
```

The chain terminates when `π` reaches the sentinel value `b'1' * 16`. The cloud stores `(c_w → {c_a, c_id, v, f_hash})` and never sees plaintext keywords or file IDs directly.

### 3. Jianding Verification Tags (Algorithm 3 — Upload)
A MAC tag `v` is generated at upload time over the index entry and file fingerprint:

```
tag_content = c_w || s3_key || SHA256(ciphertext)
v = HMAC-SHA256(kv, tag_content)
```

This tag travels with the index entry to EC2 and is used to detect index tampering during search.

### 4. Trapdoor Generation (Algorithm 4)
During search, the client generates a trapdoor `(kt1, π_current)` from the latest local state and sends it to EC2. The server uses `kt1` and `π` to traverse the XOR chain without ever learning the keyword.

### 5. Search & Chain Traversal (Algorithm 5 — EC2 Server)
The EC2 server walks the chain using:
```
c_w = SHA256(π_current)
mask = SHA256(kt1 || π_current)
r = c_a XOR mask
π_next = π_current XOR r
```
It returns all matched entries plus `final_π` for completeness verification.

### 6. Dual-Layer Jianding Verification (Search — Client Side)
For every result returned from EC2:

- **Layer 1 — Index Integrity**: Recomputes `HMAC-SHA256(kv, c_w || s3_key || f_hash)` and checks it matches `v`. A failure indicates the index on EC2 was tampered.
- **Layer 2 — Storage Integrity**: Downloads the ciphertext from S3, computes `SHA256(ciphertext)`, and compares against `f_hash`. A failure indicates the file in S3 was modified or replaced.
- **Completeness Check**: Verifies `final_π == b'1' * 16` (stop signal), confirming no entries were silently dropped from the chain.

### 7. File Decryption (Algorithm 6)
Decryption happens entirely client-side using `k2` derived from the original filename as the AES-GCM key. The server has no decryption capability.

---

## HTV-DSSE: Hierarchical Access Control

**`hierarchical_secret_sharing.py`** implements a two-level Shamir's Secret Sharing tree that controls who can unlock the master database trapdoor key:

```
ROOT KEY (requires 2 of 2 departments)
├── Admin Dept Key   (requires 1 of 2 admins)
└── Engineering Dept Key (requires 3 of 5 engineers)
```

- The root master key is split into department shares using Shamir's scheme over a 521-bit Mersenne prime field.
- Each department key is further split into user shares.
- Recovery is bottom-up: user shares → department keys → root master key.
- A search can only be initiated when the threshold for both departments is met.

**`htv_dsse.py`** provides a simplified demo of the same concept using the `secretsharing` library.

---

## Architecture

```
┌──────────────────────────────────┐
│         Client (Local)           │
│  Flask UI  ─►  scs_client.py    │
│  Key Derivation (encryption.py) │
│  Local State: local_hexie_state  │
└────────────┬─────────────────────┘
             │ HTTPS / REST
     ┌───────┴────────────┐
     │     EC2 Server     │         ┌───────────────┐
     │   ec2_server.py    │◄───────►│  Amazon S3    │
     │  cloud_index.json  │         │ (ciphertext)  │
     └────────────────────┘         └───────────────┘
```

| Component | Role |
|---|---|
| **Client (Flask app)** | Handles uploads, key derivation, XOR-chain construction, Jianding tag generation, and file decryption |
| **EC2 Server (`ec2_server.py`)** | Stores and serves the encrypted inverted index; implements chain traversal (Algorithm 5) |
| **Amazon S3** | Stores raw ciphertext blobs only; no plaintext or metadata |
| **Local State (`local_hexie_state.json`)** | Tracks the latest `π` per keyword so the client can construct new chain links on future uploads |

---

## Module Reference

### Application Core (`app/`)

| Module | Purpose |
|---|---|
| `app.py` | Flask entry point. Exposes `/`, `/upload`, `/search`, `/download`, and a live `/stream-logs` SSE endpoint for real-time console output in the browser UI. |
| `scs_client.py` | Upload pipeline: keyword extraction, XOR-chain index construction, Jianding tag generation, AES-GCM encryption, S3 upload, and EC2 index update. |
| `scs_search.py` | Search pipeline: trapdoor generation, EC2 chain traversal, dual-layer Jianding verification (index MAC + S3 content hash + completeness), and client-side decryption. |
| `encryption.py` | Key derivation (`derive_keys`) and AES-GCM file encryption/decryption. Implements Algorithms 1, 2, and 6. |
| `aws_client.py` | Thin boto3 wrapper for S3 upload and download. |
| `ec2_server.py` | Flask server deployed on EC2. Implements the `/update` (Algorithm 2 store) and `/search` (Algorithm 5 chain traversal) endpoints. |
| `hexie.py` | Legacy trapdoor helper. Loads local `di_state` and returns `(kt1, π)` for a keyword. |
| `jianding.py` | Reserved for standalone Jianding verification utilities. |
| `hexie_chain_visualiser.py` | Developer utility to visualise the XOR chain structure in `local_hexie_state.json`. |
| `hexie_inspector.py` | Developer utility to inspect individual chain entries. |
| `local_server.py` | Local EC2 simulation server for offline/testing use. |
| `scs_cleanup.py` | Cleanup utility. Clears local state files, downloads, and optionally empties the S3 bucket. |
| `full_cleanup.py` | Full reset: clears S3, EC2 index, and all local state. |

### Research / Access Control Scripts (root)

| Module | Purpose |
|---|---|
| `hierarchical_secret_sharing.py` | Pure-Python Shamir's Secret Sharing over a 521-bit prime field. Implements a two-level hierarchical tree (departments → users) for unlocking the master trapdoor key. |
| `htv_dsse.py` | Alternative HTV-DSSE demo using the `secretsharing` library. Demonstrates the same department/user threshold access model. |

### UI Templates (`app/templates/`)

| File | Purpose |
|---|---|
| `index.html` | Landing dashboard. Shows current S3 file count. |
| `upload.html` | Upload interface with live console (SSE stream) showing encryption, keyword extraction, and S3 progress. |
| `search.html` | Search interface. Displays Jianding verification results alongside matched files and provides a download button. |

### Infrastructure (`infrastructure/terraform/`)

| File | Purpose |
|---|---|
| `main.tf` | Provisions the AWS provider, S3 bucket, EC2 instance (for hosting `ec2_server.py`), and security group (ports 22, 80, 443, 5000). |
| `variables.tf` | Terraform input variable declarations. |
| `outputs.tf` | Terraform output definitions (e.g., public EC2 IP). |

---

## Local State Files

| File | Description |
|---|---|
| `local_hexie_state.json` | Maps each keyword to its latest `π` (XOR chain state). Updated after every upload. Required for future uploads and all search operations. |
| `cloud_index.json` | A local mirror of the EC2 encrypted index (`c_w → entry`). Used by the local simulation server. |
| `downloads/` | Decrypted and restored files after a successful search and download. |
| `temp_uploads/` | Temporary storage for ciphertext during the upload pipeline. Cleaned up after S3 upload. |

> **Important:** `local_hexie_state.json` is the single most critical local file. If it is lost, existing chain links cannot be extended and previously uploaded files cannot be retrieved.

---

## Setup

### Prerequisites

- Python 3.10+
- AWS account with an IAM user/role that has `s3:GetObject`, `s3:PutObject`, and `s3:ListBucket` permissions
- An EC2 instance running `ec2_server.py` (or use `local_server.py` for local testing)
- An S3 bucket (name configured in `.env`)

### Install Dependencies

```bash
cd app
pip install -r requirements.txt
```

### Configure Environment

Create `app/.env`:

```env
S3_BUCKET_NAME=your-bucket-name
EC2_HOSTNAME=your-ec2-public-ip
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_DEFAULT_REGION=ap-south-1
```

### Run the Flask App (Client)

```bash
cd app
python app.py
```

Open `http://127.0.0.1:5030` in the browser.

### Run the EC2 Index Server

On the EC2 instance (or locally for testing):

```bash
python ec2_server.py
# Listens on 0.0.0.0:5000
```

For local offline testing, use `local_server.py` instead and set `EC2_HOSTNAME=127.0.0.1` in `.env`.

---

## Deployment

Infrastructure is managed with Terraform in `infrastructure/terraform/`.

```bash
cd infrastructure/terraform
terraform init
terraform apply
```

The Terraform plan provisions:
- An S3 bucket for encrypted file storage
- An EC2 instance for the Hexie index server
- A security group allowing HTTP (80), HTTPS (443), Flask (5000), and restricted SSH (22) access

GitHub Actions (`.github/workflows/deploy.yml`) runs `terraform apply` automatically on pushes to `main`.

---

## Demonstration: HTV-DSSE Access Control

Run the hierarchical secret sharing demo to see threshold-based key recovery:

```bash
python hierarchical_secret_sharing.py
```

Expected output:
```
Original Master Key: REAL_AES256_DB_TRAPDOOR

[SYSTEM] Locking tree...
Tree LOCKED. User shares distributed.

--- TEST 1: Valid Threshold (1 Admin, 3 Engineers) ---
[+] Successfully reconstructed Admin Department Key.
[+] Successfully reconstructed Engineering Department Key.
[SUCCESS] ROOT MASTER KEY DECRYPTED: REAL_AES256_DB_TRAPDOOR

--- TEST 2: Invalid Threshold (1 Admin, only 2 Engineers) ---
[-] Failed to reconstruct Engineering Department Key (not enough valid shares).
[FAILURE] Could not reconstruct tree: Not enough department thresholds met to unlock root key.
```

---

## Security Notes

- The `MASTER_KEY` in `encryption.py` is a fixed test key. Replace it with a securely generated and stored key before any serious deployment.
- `local_hexie_state.json` must be kept secure and backed up. It is the client's exclusive knowledge of the XOR chain state.
- The EC2 server learns nothing about keywords, filenames, or file contents — it only processes encrypted pointers and returns encrypted entries.
- Jianding tags bind the index entry, the S3 object key, and the file content hash together under `kv`. Any modification to any of these three fields will cause verification to fail.

---

## Requirements

```
Flask
boto3
cryptography
PyPDF2
requests
python-dotenv
secretsharing   # for htv_dsse.py only
```

---

## License

MIT License. See `LICENSE` for details.
