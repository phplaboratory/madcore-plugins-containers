FROM ubuntu:latest

# Update OS

RUN apt-get update
RUN apt-get -y upgrade


RUN apt-get install -y python-dev python-pip
RUN apt-get install -y libffi-dev libssl-dev

RUN pip install flanker
RUN pip install elasticsearch


# Add requirements.txt
RUN mkdir /opt/mailgun-flanker
ADD 2es.py /opt/mailgun-flanker/2es.py


# Set the default directory for our environment
ENV HOME /opt/mailgun-flanker

ENV EMAILS_PATH /var/mailgun-flanker
ENV ELASTICSEARCH "http://localhost:9200"
ENV ELASTICSEARCH_INDEX  "mailgun-flanker"

WORKDIR /opt/mailgun-flanker

CMD /usr/bin/python2.7 /opt/mailgun-flanker/2es.py