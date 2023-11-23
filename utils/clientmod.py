from . import mongo_utils, user_io
import json
import os
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor
import sys

def remove_temp_files():
    save_path = "./cache/"
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