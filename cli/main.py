from utils import user_io
from utils import mongo_utils
import json

with open("uri_list.json", "r") as f:
    uri_list = json.load(f)["uri_list"]

client_list = mongo_utils.connect_mongo_cluster(uri_list)

user_io.print_welcome()

while True:
    user_input = input("Please enter the command：")
    user_io.parse_input(user_input, client_list)
