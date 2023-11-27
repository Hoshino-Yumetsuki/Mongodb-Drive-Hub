FROM python:3.11

RUN apt-get update && apt-get install -y git && pip install --upgrade pip

RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
	PATH=/home/user/.local/bin:$PATH

WORKDIR $HOME/app

RUN git clone https://github.com/Anjiurine/Mongodb-Drive-Hub.git

WORKDIR $HOME/app/Mongodb-Drive-Hub

ADD --chown=user ./uri_list.json $HOME/app/Mongodb-Drive-Hub/uri_list.json

RUN pip install -r requirements.txt

EXPOSE 19198

RUN chown -R user:user ./

CMD ["python", "mdh.py", "-s"]
