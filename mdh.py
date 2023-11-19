from utils import user_io
from utils import mongo_utils
import json
import os
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor

if __name__ == "__main__":
    try:
        if os.path.exists('./uri_list.json') == False:
            print("uri_list.json not found")
            exit()
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
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}\n{traceback.format_exc()}")
