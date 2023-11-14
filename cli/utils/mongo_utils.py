import base64
import hashlib
from pymongo import MongoClient
import py7zr
import os

def connect_mongo_cluster(uri_list):
    client_list = []
    for uri in uri_list:
        client = MongoClient(uri)
        client_list.append(client)
    return client_list

# mongo_utils.py
def upload_file(client_list, file_path):
    with open(file_path, "rb") as f:
        file_data = f.read()
    file_sha256 = hashlib.sha256(file_data).hexdigest()
    file_name, file_ext = os.path.basename(file_path).split(".")
    file_size = os.path.getsize(file_path)
    file_7z_path = file_path + ".7z"
    with py7zr.SevenZipFile(file_7z_path, 'w') as archive:
        archive.write(file_path, file_name + "." + file_ext)
    file_7z_size = os.path.getsize(file_7z_path)
    file_7z_data = open(file_7z_path, "rb").read()
    os.remove(file_7z_path)
    num_of_clients = len(client_list)
    chunk_size = file_7z_size // num_of_clients
    for i in range(num_of_clients):
        client = client_list[i]
        db = client["files"]
        col = db["files"]
        start = i * chunk_size
        end = (i + 1) * chunk_size if i < num_of_clients - 1 else file_7z_size
        chunk_data = file_7z_data[start:end]
        chunk_data_b64 = base64.b64encode(chunk_data)
        chunk_sha256 = hashlib.sha256(chunk_data).hexdigest()
        chunk_doc = {
            "name": file_name,
            "ext": file_ext,
            "sha256": file_sha256,
            "chunk_no": i + 1,
            "data": chunk_data_b64,
            "size": file_size,
            "total_chunks": num_of_clients,
            "chunk_sha256": chunk_sha256
        }
        col.insert_one(chunk_doc)
    return file_sha256


def download_file(client_list, file_sha256, save_path):
    file_7z_data = b""
    file_name = None
    file_ext = None
    file_size = None
    total_chunks = None
    for client in client_list:
        db = client["files"]
        col = db["files"]
        chunk_doc = col.find_one({"sha256": file_sha256})
        if chunk_doc:
            file_name = chunk_doc["name"]
            file_ext = chunk_doc["ext"]
            file_size = chunk_doc["size"]
            total_chunks = chunk_doc["total_chunks"]
            chunk_data_b64 = chunk_doc["data"]
            chunk_data = base64.b64decode(chunk_data_b64)
            file_7z_data += chunk_data
        else:
            return None
    file_7z_path = save_path + file_name + "." + file_ext + ".7z"
    with open(file_7z_path, "wb") as f:
        f.write(file_7z_data)
    with py7zr.SevenZipFile(file_7z_path, 'r') as archive:
        archive.extractall(save_path)
    os.remove(file_7z_path)
    file_path = save_path + file_name + "." + file_ext
    return file_path

def list_files(client_list):
    file_list = []
    client = client_list[0]
    db = client["files"]
    col = db["files"]
    for chunk_doc in col.find({"chunk_no": 1}):
        file_name = chunk_doc["name"]
        file_ext = chunk_doc["ext"]
        file_path = file_name + "." + file_ext
        file_size = chunk_doc["size"]
        file_sha256 = chunk_doc["sha256"]
        total_chunks = chunk_doc["total_chunks"]
        file_info = {
            "path": file_path,
            "name": file_name + "." + file_ext,
            "size": file_size,
            "sha256": file_sha256,
            "total_chunks": total_chunks
        }
        file_list.append(file_info)
    return file_list

def delete_file(client_list, file_sha256):
    result = True
    for client in client_list:
        db = client["files"]
        col = db["files"]
        chunk_doc = col.find_one_and_delete({"sha256": file_sha256})
        if not chunk_doc:
            result = False
    return result

def reindex_file(client_list):
    result = False
    file_list = list_files(client_list)
    for file_info in file_list:
        file_sha256 = file_info["sha256"]
        file_path = download_file(client_list, file_sha256, "./cache")
        if file_path:
            os.remove(file_path)
            delete_file(client_list, file_sha256)
            upload_file(client_list, file_path)
            result = True
    return result

def search_file(client_list, keyword):
    file_list = []
    client = client_list[0]
    db = client["files"]
    col = db["files"]
    for chunk_doc in col.find({"chunk_no": 1, "$or": [{"name": keyword}, {"name": {"$regex": keyword}}]}):
        file_name = chunk_doc["name"]
        file_ext = chunk_doc["ext"]
        file_path = file_name + "." + file_ext
        file_size = chunk_doc["size"]
        file_sha256 = chunk_doc["sha256"]
        total_chunks = chunk_doc["total_chunks"]
        file_info = {
            "path": file_path,
            "name": file_name + "." + file_ext,
            "size": file_size,
            "sha256": file_sha256,
            "total_chunks": total_chunks
        }
        file_list.append(file_info)
    return file_list
