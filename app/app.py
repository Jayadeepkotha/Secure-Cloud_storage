import os
from flask import Flask, render_template, request, jsonify
from scs_client import run_upload, load_json_state, DI_MAP
from scs_search import perform_search, decrypt_and_save

app = Flask(__name__)
UPLOAD_FOLDER = 'temp_uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        file = request.files.get('file')
        if not file: return jsonify({"error": "No file"}), 400
        
        file_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(file_path)
        try:
            run_upload(file_path)
            os.remove(file_path)
            return jsonify({"success": True, "message": "Encrypted & Uploaded Successfully!"})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return render_template('upload.html')

@app.route('/search', methods=['GET', 'POST'])
def search_page():
    if request.method == 'POST':
        keyword = request.form.get('keyword', '')
        results = perform_search(keyword)
        return jsonify({"results": results})
    return render_template('search.html')

from flask import send_file
import io

@app.route('/download', methods=['POST'])
def download_file_route():
    data = request.get_json()
    try:
        # 1. Decrypt the file logic (this should return bytes)
        # Assuming decrypt_and_save returns the local path as before:
        path = decrypt_and_save(data['selected'], data['keyword'])
        
        if path and os.path.exists(path):
            # 2. Send the file back to the browser
            return send_file(
                os.path.abspath(path),
                as_attachment=True,
                download_name=data['selected']['original']
            )
        return jsonify({"success": False, "error": "File not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
if __name__ == '__main__':
    app.run(port=5000, debug=True)