#!/usr/bin/env python

from __future__ import print_function, unicode_literals

from slacker import Slacker
import argparse
import json

SLACK_ACTIONS = ['post_message', 'pull_messages']


def parse_args():
    """
    Parse arguments for input params
    """

    parser = argparse.ArgumentParser(prog="Jenkins Scheduler Generator")

    parser.add_argument('-a', '--action', required=True, choices=SLACK_ACTIONS,
                        help='Slack API action to perform')
    parser.add_argument('-t', '--token', required=True, help='Slack API token')
    parser.add_argument('-p', '--payload', required=True, help='Slack API payload for specific action')
    parser.add_argument('-d', '--debug', default=False, action='store_true')

    return parser.parse_args()


class SlackApi(object):
    def __init__(self, settings):
        self.settings = settings
        self.slack = Slacker(self.settings.token)
        self.payload = self.validate_payload()

    def validate_payload(self):
        return json.loads(self.settings.payload)

    def log(self, msg):
        print(msg)

    def save(self, data):
        with open('./data.json', 'w') as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=False).encode('utf-8'))

    def post_message(self):
        r = self.slack.chat.post_message(self.payload['channel'], self.payload['text'], **self.payload.get('args', {}))
        self.log(r.body)
        return r

    def pull_messages(self):
        channel_id = self.slack.channels.get_channel_id(self.payload['channel'])
        r = self.slack.channels.history(channel_id)
        self.save(r.body)
        print(r)

    def run(self):
        return getattr(self, self.settings.action)()


if __name__ == '__main__':
    SlackApi(parse_args()).run()
