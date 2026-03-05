import os
from flask import Flask, render_template

# This tells Flask exactly where to look relative to this file
base_dir = os.path.abspath(os.path.dirname(__file__))
template_dir = os.path.join(base_dir, 'templates')

app = Flask(__name__, template_folder=template_dir)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload')
def upload():
    return render_template('upload.html')

@app.route('/search')
def search():
    return render_template('search.html')

if __name__ == '__main__':
    # Using port 5001 in case 5000 is blocked by your system
    app.run(debug=True, port=5006)