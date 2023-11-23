import base64
import hashlib
from pymongo import MongoClient
import py7zr
import os
from threading import Lock
import traceback
import logging
from concurrent.futures import ThreadPoolExecutor
import tabulate

logging.basicConfig(level=logging.INFO)

lock = Lock()

def upload_wrapper(args):
    client_list, file_path = args
    try:
        with lock:
            upload_result = upload_file(client_list, file_path)
        return upload_result
    except Exception as e:
        logging.error(f"Error uploading file: {file_path}\n{traceback.format_exc()}")
        return None

def download_wrapper(args):
    client_list, file_sha256, save_path = args
    try:
        with lock:
            download_result = download_file(client_list, file_sha256, save_path)
        return download_result
    except Exception as e:
        logging.error(f"Error downloading file: {file_sha256}\n{traceback.format_exc()}")
        return None

def connect_mongo_cluster(uri_list):
    client_list = []
    def connect(uri):
        return MongoClient(uri, maxPoolSize=16)
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(connect, uri) for uri in uri_list]
        for future in futures:
            client = future.result()
            client_list.append(client)
    return client_list

def upload_file(client_list, file_path):
    file_path = os.path.abspath(file_path)
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
    chunk_docs = []
    for client in client_list:
        db = client["files"]
        col = db["files"]
        chunk_docs.extend(col.find({"sha256": file_sha256}).sort("chunk_no"))
    for chunk_doc in chunk_docs:
        if not file_name:
            file_name = chunk_doc["name"]
            file_ext = chunk_doc["ext"]
            file_size = chunk_doc["size"]
            total_chunks = chunk_doc["total_chunks"]
        chunk_data_b64 = chunk_doc["data"]
        chunk_data = base64.b64decode(chunk_data_b64)
        file_7z_data += chunk_data
    file_7z_path = os.path.join(save_path, f"{file_name}.{file_ext}.7z")
    with open(file_7z_path, "wb") as f:
        f.write(file_7z_data)

    with py7zr.SevenZipFile(file_7z_path, 'r') as archive:
        archive.extractall(save_path)
    os.remove(file_7z_path)
    file_path = os.path.join(save_path, f"{file_name}.{file_ext}")
    return file_path

def list_files(client_list, cli_output=True):
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

    if cli_output:
        headers = ["Name", "Size", "SHA256", "Total Chunks"]
        table_data = [(f["name"], f["size"], f["sha256"], f["total_chunks"]) for f in file_list]
        print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        return file_list

def delete_file(client_list, file_sha256):
    total_clients = len(client_list)
    deleted_chunks = set()
    for client in client_list:
        db = client["files"]
        col = db["files"]
        result = col.find_one_and_delete({"sha256": file_sha256})
        if result:
            deleted_chunks.add(result["chunk_no"])
    if len(deleted_chunks) == total_clients:
        return True
    else:
        return False

def search_file(client_list, keyword, cli_output=True):
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

    if cli_output:
        headers = ["Name", "Size", "SHA256", "Total Chunks"]
        table_data = [(f["name"], f["size"], f["sha256"], f["total_chunks"]) for f in file_list]
        print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        return file_list

def get_storage_info(client_list, selected_instance=None, cli_output=True):
    total_storage = 0
    total_free_storage = 0
    total_used_storage = 0
    storage_info_list = []

    for i, client in enumerate(client_list, start=1):
        if selected_instance is not None and i != selected_instance:
            continue

        db = client.files
        stats = db.command('dbstats')
        storage_info = {
            "instance_uri": client.address[0],
            "total_storage": stats["storageSize"],
            "free_storage": stats["storageSize"] - stats["dataSize"],
            "used_storage": stats["dataSize"]
        }
        storage_info_list.append(storage_info)

        total_storage += stats["storageSize"]
        total_free_storage += stats["storageSize"] - stats["dataSize"]
        total_used_storage += stats["dataSize"]

        if selected_instance is not None:
            break

    if selected_instance is None:
        storage_info_list = {
            "total_storage": total_storage,
            "free_storage": total_free_storage,
            "used_storage": total_used_storage
        }

    if cli_output:
        headers = ["Instance URI", "Total Storage", "Free Storage", "Used Storage"]
        table_data = [(info["instance_uri"], info["total_storage"], info["free_storage"], info["used_storage"]) for info in storage_info_list]
        print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        return storage_info_list

def reindex_files(client_list, save_path='./cache'):
    if not os.path.exists(save_path):
        os.makedirs(save_path)
    file_list = list_files(client_list, cli_output=False)
    for file_info in file_list:
        file_sha256 = file_info["sha256"]
        file_name = file_info["name"]
        file_path = os.path.join(save_path, file_name)
        downloaded_file_path = download_file(client_list, file_sha256, save_path)
        delete_file(client_list, file_sha256)
        if downloaded_file_path:
            upload_file(client_list, downloaded_file_path)
        os.remove(downloaded_file_path)

def dbstatus(client_list, cli_output=True):
    status_result = {}

    for client in client_list:
        uri = client.address[0]
        try:
            db = client.test
            db.command('ping')
            status_result[uri] = "connected"
        except Exception as e:
            status_result[uri] = "disconnected"

    if cli_output:
        headers = ["Instance URI", "Status"]
        table_data = [(uri, status) for uri, status in status_result.items()]
        print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
    else:
        return status_result

def retry_connect(client_list, db_name):
    try:
        client = MongoClient(db_name, maxPoolSize=16)
        client_list.append(client)
        return True
    except Exception as e:
        return False