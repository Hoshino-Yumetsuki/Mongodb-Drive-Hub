FROM python:3.11

RUN apt-get update && apt-get install -y git && pip install --upgrade pip

RUN git clone https://github.com/Anjiurine/Mongodb-Drive-Hub.git

WORKDIR /Mongodb-Drive-Hub

ADD ./uri_list.json /Mongodb-Drive-Hub/uri_list.json

RUN pip install -r requirements.txt

EXPOSE 19198

CMD ["python", "mdh.py", "-s"]