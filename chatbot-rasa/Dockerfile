FROM ubuntu:22.04

USER root

WORKDIR /app

COPY . .

RUN  apt update -y && apt upgrade -y &&\
     apt install -y build-essential libssl-dev libffi-dev python3-dev software-properties-common &&\
     add-apt-repository ppa:deadsnakes/ppa &&\
     apt update -y &&\
     apt install python3.10 python3-pip -y &&\
     python3.10 -m pip install -r requirements.txt &&\
     python3.10 -m pip install -r requirements-actions.txt &&\
     useradd -u 1001 -d /app rasa &&\
     python3.10 -m spacy download el_core_news_md &&\
     rasa train --force &&\
     chown 1001:1001 /app -R &&\
     apt clean -y

USER 1001

EXPOSE 5005
EXPOSE 5055

ENTRYPOINT ["./entrypoint.sh"]
