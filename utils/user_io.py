import sys
import os
from . import mongo_utils
from time import sleep
import tabulate

def print_welcome():
    print("You can use the following commands to manipulate files:")
    print("up or upload <file_path> - Upload files to mongodb cluster")
    print("dl or download <file_sha256> - Download files from mongodb cluster")
    print("ls or list - View file list in mongodb cluster")
    print("rm or remove <file_sha256> - Remove files from mongodb cluster")
    print("se or search <keyword> - Search files")
    print("exit - Exit the program")

def print_error(error):
    print(f"Error: {error}")

def print_success(message):
    print(f"Successful operation: {message}")

def parse_input(user_input, client_list):
    user_input = user_input.split()
    try:
        try:
            command = user_input[0]
        except Exception as e:
            print_error("Invalid command or argument")

        if command == "up" or command == "upload" and len(user_input) == 2:
            try:
                file_path = user_input[1].strip('"').replace("\\", "/")
            except Exception as e:
                print_error("Invalid command or argument")
            try:
                file_sha256 = mongo_utils.upload_file(client_list, file_path)
                print_success(f"\nThe file has been uploaded and the file sha256 is: {file_sha256}")
            except Exception as e:
                print_error(e)

        elif command == "dl" or command == "download" and len(user_input) == 2:
            try:
                file_sha256 = user_input[1]
            except Exception as e:
                print_error("Invalid command or argument")
            if os.path.exists('./download') == False:
                os.mkdir('./download')
            save_path = "./download/"
            try:
                file_path = mongo_utils.download_file(client_list, file_sha256, save_path)
                if file_path:
                    print_success(f"\nThe file has been downloaded and the file path is: {file_path}")
                else:
                    print_error("File does not exist")
            except Exception as e:
                print_error(e)

        elif command == "ls" or command == "list" and len(user_input) == 1:
            try:
                file_list = mongo_utils.list_files(client_list, cli_output=False)
                if file_list:
                    headers = ["Name", "Size", "SHA256", "Total Chunks"]
                    table_data = [(f["name"], f["size"], f["sha256"], f["total_chunks"]) for f in file_list]
                    print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
                else:
                    print_error("No file")
            except Exception as e:
                print_error(e)

        elif command == "rm" or command == "remove" and len(user_input) == 2:
            try:
                file_sha256 = user_input[1]
            except Exception as e:
                print_error("Invalid command or argument")
            try:
                result = mongo_utils.delete_file(client_list, file_sha256)
                if result:
                    print_success("The file has been deleted")
                else:
                    print_error("File does not exist")
            except Exception as e:
                print_error(e)

        elif command == "se" or command == "search" and len(user_input) == 2:
            try:
                keyword = user_input[1]
            except Exception as e:
                print_error("Invalid command or argument")
            try:
                file_list = mongo_utils.search_file(client_list, keyword, cli_output=False)
                if file_list:
                    headers = ["Name", "Size", "SHA256", "Total Chunks"]
                    table_data = [(f["name"], f["size"], f["sha256"], f["total_chunks"]) for f in file_list]
                    print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
                else:
                    print_error("No file matches the keyword")
            except Exception as e:
                print_error(e)

        elif command == "re" or command == "reindex" and len(user_input) == 1:
            confirmation = input("Are you sure you want to reindex all files? This will download and re-upload all files. (y/n): ").lower()
            if confirmation == 'yes' or confirmation == 'y':
                try:
                    mongo_utils.reindex_files(client_list)
                    print_success("Reindex completed successfully.")
                except Exception as e:
                    print_error("Error during reindexing.")
                    print_error(e)
            else:
                print("Reindex operation canceled.")

        elif command == "ds" or command == "dbstatus" and len(user_input) == 1:
            try:
                status_result = mongo_utils.dbstatus(client_list, cli_output=False)
                if status_result:
                    headers = ["Instance URI", "Status"]
                    table_data = [(uri, status) for uri, status in status_result.items()]
                    print(tabulate.tabulate(table_data, headers=headers, tablefmt="grid"))
                else:
                    print_error("Failed to retrieve database status")
            except Exception as e:
                print_error("Error during dbstatus.")
                print_error(e)

        elif command == "exit":
            sys.exit()

        else:
            print_error("Invalid command or argument")
    except Exception as e:
        sleep(0)
