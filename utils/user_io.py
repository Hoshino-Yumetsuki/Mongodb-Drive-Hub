import sys
from . import mongo_utils

def print_welcome():
    print("You can use the following commands to manipulate files:")
    print("upload <file_path> - Upload files to mongodb")
    print("download <file_sha256> - Download files from mongodb")
    print("list - View file list in mongodb")
    print("exit - Exit the program")

def print_error(error):
    print("An error occurred：", error)

def print_success(message):
    print("Successful operation：", message)

def parse_input(user_input, client):
    user_input = user_input.split()
    command = user_input[0]
    if command == "upload" and len(user_input) == 2:
        file_path = user_input[1]
        db_name = "files"
        col_name = "files"
        try:
            file_id = mongo_utils.upload_file(client, db_name, col_name, file_path)
            print_success("The file has been uploaded and the file id is:" + str(file_id))
        except Exception as e:
            print_error(e)
    elif command == "download" and len(user_input) == 2:
        file_sha256 = user_input[1]
        db_name = "files"
        col_name = "files"
        save_path = "./"
        try:
            file_path = mongo_utils.download_file(client, db_name, col_name, file_sha256, save_path)
            if file_path:
                print_success("The file has been downloaded and the file path is:" + file_path)
            else:
                print_error("File does not exist")
        except Exception as e:
            print_error(e)
    elif command == "list" and len(user_input) == 1:
        db_name = "files"
        col_name = "files"
        try:
            file_list = mongo_utils.list_files(client, db_name, col_name)
            if file_list:
                print_success("The file list is as follows:")
                for file_info in file_list:
                    print("File path:", file_info["path"])
                    print("File name:", file_info["name"])
                    print("File size:", file_info["size"])
                    print("File sha256:", file_info["sha256"])
                    print("--------------------")
            else:
                print_error("No file")
        except Exception as e:
            print_error(e)
    elif command == "exit":
        sys.exit()
    else:
        print_error("Invalid command or argument")
