# app/utils.py
import os
from werkzeug.utils import secure_filename
from flask import current_app

def save_image(file):
    if file:
        # Create uploads directory if it doesn't exist
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder) # This creates the directory if missing

        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath) # This saves the FileStorage object to disk
        return filename # This MUST return ONLY the filename string
    return None