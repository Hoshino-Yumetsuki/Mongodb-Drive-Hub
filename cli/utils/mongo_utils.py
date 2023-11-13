# mongo_utils.py
import base64
import hashlib
from pymongo import MongoClient

def connect_mongo(mongo_uri):
    client = MongoClient(mongo_uri)
    return client

def upload_file(client, db_name, col_name, file_path):
    with open(file_path, "rb") as f:
        file_data = f.read()
    file_data_b64 = base64.b64encode(file_data)
    file_sha256 = hashlib.sha256(file_data).hexdigest()
    file_name, file_ext = file_path.split(".")
    file_doc = {
        "name": file_name,
        "ext": file_ext,
        "sha256": file_sha256,
        "data": file_data_b64
    }
    db = client[db_name]
    col = db[col_name]
    col.insert_one(file_doc)
    return file_doc["_id"]

def download_file(client, db_name, col_name, file_sha256, save_path):
    db = client[db_name]
    col = db[col_name]
    file_doc = col.find_one({"sha256": file_sha256})
    if file_doc:
        file_data_b64 = file_doc["data"]
        file_data = base64.b64decode(file_data_b64)
        file_name = file_doc["name"]
        file_ext = file_doc["ext"]
        file_path = save_path + file_name + "." + file_ext
        with open(file_path, "wb") as f:
            f.write(file_data)
        return file_path
    else:
        return None

def list_files(client, db_name, col_name):
    db = client[db_name]
    col = db[col_name]
    file_list = []
    for file_doc in col.find():
        file_name = file_doc["name"]
        file_ext = file_doc["ext"]
        file_path = db_name + "/" + col_name + "/" + file_name + "." + file_ext
        file_size = len(file_doc["data"])
        file_sha256 = file_doc["sha256"]
        file_info = {
            "path": file_path,
            "name": file_name + "." + file_ext,
            "size": file_size,
            "sha256": file_sha256
        }
        file_list.append(file_info)
    return file_list

def delete_file(client, db_name, col_name, file_sha256):
    db = client[db_name]
    col = db[col_name]
    file_doc = col.find_one_and_delete({"sha256": file_sha256})
    if file_doc:
        return True
    else:
        return False
