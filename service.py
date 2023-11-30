from utils import mongo_utils, user_io
import json
import os
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor
import sys
import atexit
import signal
import asyncio
from quart import Quart, render_template, jsonify, request, after_this_request, Response
import mimetypes
from quart.helpers import send_file as quart_send_file
import aiofiles
from hypercorn.config import Config
from hypercorn.asyncio import serve

client_list = []

def remove_temp_files():
    save_path = "./cache/"
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    for file_name in os.listdir(save_path):
        file_path = os.path.join(save_path, file_name)
        try:
            os.unlink(file_path)
        except Exception as e:
            logging.warning(f"Error removing temporary file: {str(e)}")

def run_cli_mode():
    try:
        if os.path.exists('./uri_list.json') == False:
            print("uri_list.json not found")
            sys.exit()
        with open("uri_list.json", "r") as f:
            uri_list = json.load(f)["uri_list"]
        client_list = mongo_utils.connect_mongo_cluster(uri_list)
        user_io.print_welcome()
        while True:
            user_input = input("Please enter the command：")
            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(user_io.parse_input, user_input, client_list)]
                for future in futures:
                    future.result()
    except KeyboardInterrupt:
        print("\nProgram terminated by user.")
        remove_temp_files()
        sys.exit(0)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}\n{traceback.format_exc()}")

app = Quart(__name__, instance_relative_config=True, template_folder='templates')

@app.route('/static/<path:filename>')
async def serve_static(filename):
    return await quart_send_file(filename, conditional=False, cache_timeout=3600)

async def async_send_file(file_path, as_attachment=False):
    async with aiofiles.open(file_path, 'rb') as file:
        file_data = await file.read()
        mime_type, _ = mimetypes.guess_type(file_path)
        headers = {"Content-Type": mime_type}
        if as_attachment:
            headers["Content-Disposition"] = f"attachment; filename={os.path.basename(file_path)}"
        return Response(file_data, headers=headers)

@app.route('/')
async def js_rendered_files():
    return await render_template('index.html')

@app.route('/status')
async def js_rendered_status():
    return await render_template('status.html')

@app.route('/download/<file_sha256>')
async def download_file(file_sha256):
    save_path = "./cache/"
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    try:
        file_path = await asyncio.to_thread(mongo_utils.download_file, client_list, file_sha256, save_path)
        if file_path:
            @after_this_request
            def remove_temp_file(response):
                return response
            return await async_send_file(file_path, as_attachment=True)
        else:
            return "File does not exist", 404
    except Exception as e:
        return str(e), 500

@app.route('/api/files')
async def api_list_files():
    search_term = request.args.get('search', '')
    file_list = await asyncio.to_thread(mongo_utils.list_files, client_list, cli_output=False)
    if search_term:
        file_list = [file for file in file_list if search_term in file['name']]
    return jsonify(file_list)

@app.route('/api/status')
async def api_get_status():
    status_result = await asyncio.to_thread(mongo_utils.dbstatus, client_list, cli_output=False)
    return jsonify(status_result)

def signal_handler(sig, frame):
    print("\nProgram terminated by user.")
    remove_temp_files()
    sys.exit(0)

async def run_server_mode():
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
        config = Config.from_mapping(
            bind=["0.0.0.0:19198"],
            workers=1,
            loglevel="info",
        )
        await serve(app, config)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}\n{traceback.format_exc()}")