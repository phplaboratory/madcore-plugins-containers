FROM python:2.7.12

RUN apt-get update
RUN apt-get install -y git
RUN pip install slacker awscli

# User for kuberntes service
ENV APP_PORT 1234

ADD madcore_slack.py /opt/madcore_slack.py
ADD madcore_slack.sh /usr/local/bin/madcore_slack
RUN chmod +x /usr/local/bin/madcore_slack

RUN mkdir -p /opt/madcore_slack_service

EXPOSE ${APP_PORT}

CMD cd /opt/madcore_slack_service && python -m SimpleHTTPServer ${APP_PORT}
