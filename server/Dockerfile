FROM python:3.6.13-slim

ARG DEBIAN_FRONTEND=noninteractive

#RUN apt-get update -qq && apt-get install -qq -y \
#    cmake ninja-build pkg-config build-essential git software-properties-common checkinstall gcc g++ python3-pip

RUN apt-get update && apt-get install -y python3-opencv -qq

RUN pip3 install --upgrade pip

COPY requirements.txt / 

RUN pip3 install -r requirements.txt

COPY ./ ./app

WORKDIR /app

EXPOSE 8083

CMD ["/bin/sh","./Procfile" ]
