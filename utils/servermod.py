import atexit
import signal
from flask import Flask, send_file, after_this_request
import os
from . import mongo_utils
import logging
import sys
import json
import traceback

app = Flask(__name__)

client_list = []

def remove_temp_files():
    save_path = "./cache/"
    for file_name in os.listdir(save_path):
        file_path = os.path.join(save_path, file_name)
        try:
            os.unlink(file_path)
        except Exception as e:
            logging.warning(f"Error removing temporary file: {str(e)}")

@app.route('/download/<file_sha256>')
def download_file(file_sha256):
    save_path = "./cache/"
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    try:
        file_path = mongo_utils.download_file(client_list, file_sha256, save_path)
        if file_path:
            @after_this_request
            def remove_temp_file(response):
                return response
            return send_file(file_path, as_attachment=True)
        else:
            return "File does not exist", 404
    except Exception as e:
        return str(e), 500

def signal_handler(sig, frame):
    print("\nProgram terminated by user.")
    remove_temp_files()
    sys.exit(0)

def run_server_mode():
    try:
        global client_list
        if os.path.exists('./uri_list.json') == False:
            print("uri_list.json not found")
            sys.exit()
        with open("uri_list.json", "r") as f:
            uri_list = json.load(f)["uri_list"]
        client_list = mongo_utils.connect_mongo_cluster(uri_list)
        atexit.register(remove_temp_files)
        signal.signal(signal.SIGINT, signal_handler)
        app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}\n{traceback.format_exc()}")