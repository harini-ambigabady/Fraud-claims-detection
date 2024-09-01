from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB Configuration
client = MongoClient("mongodb://localhost:27017/")
db = client['cts']
collection_company_1 = db['documents']
collection_company_2 = db['requests']

# Folder where files will be stored
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Company 1 - Upload Page
@app.route('/user_hospital', methods=['GET', 'POST'])
def user_hospital():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Save document info in MongoDB (Company 1)
            collection_company_1.insert_one({"filename": filename, "file_path": file_path})

            # Create a request in Company 2's queue
            collection_company_2.insert_one({"filename": filename, "file_path": file_path, "status": "requested"})

            return redirect(url_for('user_hospital'))

    return render_template('user_hospital.html')

# Company 2 - Request Queue Page
@app.route('/insurance', methods=['GET'])
def insurance():
    # Fetch requests from MongoDB in FIFO order
    requests = list(collection_company_2.find().sort('_id', 1))

    return render_template('insurance.html', requests=requests)

if __name__ == '__main__':
    app.run(debug=True)
