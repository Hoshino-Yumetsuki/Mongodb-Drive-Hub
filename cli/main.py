from utils import user_io
from utils import mongo_utils

mongo_uri = "<your_mongodb_uri>"

client = mongo_utils.connect_mongo(mongo_uri)

user_io.print_welcome()

while True:
    user_input = input("Please enter the command：")
    user_io.parse_input(user_input, client)
