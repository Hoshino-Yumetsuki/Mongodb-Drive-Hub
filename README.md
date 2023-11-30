<div align="center">

<h1>Mongodb-Drive-Hub</h1>

<i>Use a high-performance Mongodb database cluster to store your files</i>

</div>

## Getting Started

### Requirements

```
pymongo
py7zr
tabulate
flask
jsonify
```


### Use

#### Use .py
- clone this repositories
- cd to cli
- install dependencies
- edit or create uri_list.json in cli
  - like this
  ```json
  {
    "uri_list": [
        "<your_db_uri>",
        "and more ..."
    ]
  }
  ```
- run python main.py

#### Use Docker

- docker build -t mongodb-drive-hub:latest . --build-arg URI_LIST=./uri_list.json
- docker run -d --name <your-container-name> -p <your-container-port>:19198 mongodb-drive-hub:latest

ps:You can even deploy it to Huggingface Space

## How to store files

![](https://github.com/Anjiurine/Mongodb-Drive-Hub/assets/147403913/5d98a626-81f5-44ed-9481-6991114ab39b)

## Special thanks

Thanks to [Tsinghua University Open Source Software Mirror Station](https://mirrors.tuna.tsinghua.edu.cn/) for inspiring my web page style development.
