FROM ubuntu:latest

# Update OS

RUN apt-get update
RUN apt-get -y upgrade


RUN apt-get install -y python-dev python-pip
RUN apt-get install -y libffi-dev libssl-dev

RUN pip install flanker
RUN pip install elasticsearch


# Add requirements.txt
RUN mkdir /opt/mailparser
ADD 2es.py /opt/mailparser/2es.py


# Set the default directory for our environment
ENV HOME /opt/mailparser

ENV EMAILS_PATH /var/maildata
ENV ELASTICSEARCH "http://localhost:9200"
ENV ELASTICSEARCH_INDEX  "polfilm-allmail"

WORKDIR /opt/mailparser

CMD /usr/bin/python2.7 /opt/mailparser/2es.py