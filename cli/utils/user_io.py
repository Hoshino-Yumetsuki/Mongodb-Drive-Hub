import sys
from . import mongo_utils

def print_welcome():
    print("You can use the following commands to manipulate files:")
    print("up or upload <file_path> - Upload files to mongodb cluster")
    print("dl or download <file_sha256> - Download files from mongodb cluster")
    print("ls or list - View file list in mongodb cluster")
    print("rm or remove <file_sha256> - Remove files from mongodb cluster")
    print("exit - Exit the program")

def print_error(error):
    print("An error occurred：", error)

def print_success(message):
    print("Successful operation：", message)

def parse_input(user_input, client_list):
    user_input = user_input.split()
    command = user_input[0]
    if command == "up" or command == "upload" and len(user_input) == 2:
        file_path = user_input[1]
        try:
            file_sha256 = mongo_utils.upload_file(client_list, file_path)
            print_success("The file has been uploaded and the file sha256 is:" + file_sha256)
        except Exception as e:
            print_error(e)
    elif command == "dl" or command == "download" and len(user_input) == 2:
        file_sha256 = user_input[1]
        save_path = "./"
        try:
            file_path = mongo_utils.download_file(client_list, file_sha256, save_path)
            if file_path:
                print_success("The file has been downloaded and the file path is:" + file_path)
            else:
                print_error("File does not exist")
        except Exception as e:
            print_error(e)
    elif command == "ls" or command == "list" and len(user_input) == 1:
        try:
            file_list = mongo_utils.list_files(client_list)
            if file_list:
                print_success("The file list is as follows:")
                for file_info in file_list:
                    print("File path:", file_info["path"])
                    print("File name:", file_info["name"])
                    print("File size:", file_info["size"])
                    print("File sha256:", file_info["sha256"])
                    print("Total chunks:", file_info["total_chunks"])
                    print("--------------------")
            else:
                print_error("No file")
        except Exception as e:
            print_error(e)
    elif command == "rm" or command == "remove" and len(user_input) == 2:
        file_sha256 = user_input[1]
        try:
            result = mongo_utils.delete_file(client_list, file_sha256)
            if result:
                print_success("The file has been deleted")
            else:
                print_error("File does not exist")
        except Exception as e:
            print_error(e)
    elif command == "exit":
        sys.exit()
    else:
        print_error("Invalid command or argument")
