from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
from pymongo import MongoClient
from flask_socketio import SocketIO, emit
from bson import ObjectId

app = Flask(__name__)
socketio = SocketIO(app)

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
            request_data = {"filename": filename, "file_path": file_path, "status": "requested"}
            inserted_id = collection_company_2.insert_one(request_data).inserted_id

            # Add the ObjectId to the data and convert it to string
            request_data["_id"] = str(inserted_id)

            # Emit an update event to all connected clients
            socketio.emit('new_request', request_data)

            return redirect(url_for('user_hospital'))

    return render_template('user_hospital.html')

# Company 2 - Request Queue Page
@app.route('/insurance', methods=['GET'])
def insurance():
    # Fetch requests from MongoDB in FIFO order
    requests = list(collection_company_2.find().sort('_id', 1))
    # Convert ObjectId to string for all requests
    for request in requests:
        request['_id'] = str(request['_id'])

    return render_template('insurance.html', requests=requests)

if __name__ == '__main__':
    socketio.run(app, debug=True)
