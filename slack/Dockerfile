FROM python:2.7.12

RUN apt-get update
RUN apt-get install -y git
RUN pip install slacker

ENV APP_PORT 1234

ADD madcore_slack.py /opt/madcore_slack.py

RUN mkdir -p /opt/madcore_slack

EXPOSE 1234

CMD cd /opt/madcore_slack && python -m SimpleHTTPServer 1234
