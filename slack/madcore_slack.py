#!/usr/bin/env python

from __future__ import print_function, unicode_literals

from slacker import Slacker
import argparse
import json
import sys
from pprint import pprint
from datetime import timedelta, datetime
import time
import os
import codecs

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
    parser.add_argument('-d', '--debug', default=False, action='store_true', help="Enable debug mode")
    parser.add_argument('-o', '--output_path', required=True, help='Specify path to save output data')

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

    def logp(self, msg):
        pprint(msg)

    def save(self, channel_name, data, timestamp):
        if not os.path.exists(self.settings.output_path):
            os.makedirs(self.settings.output_path)

        dt = datetime.fromtimestamp(timestamp)
        file_path = os.path.join(self.settings.output_path,
                                 'madcore.{}.{}.json'.format(channel_name, dt.strftime("%Y-%m-%d")))
        with codecs.open(file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=False))

        return file_path

    def post_message(self):
        r = self.slack.chat.post_message(self.payload['channel'], self.payload['text'], **self.payload.get('args', {}))
        self.log(r.body)
        return r

    def pull_messages(self):
        self.log("Get history of channel: {}".format(self.payload['channel']))

        channel_id = self.slack.channels.get_channel_id(self.payload['channel'])
        channel_info = self.slack.channels.info(channel_id).body

        if 'latest' not in channel_info['channel']:
            self.log("Seems that there are no messages in channel: '{}'".format(channel_id))
            self.logp(channel_info)
            sys.exit(1)

        latest = float(
            channel_info['channel']['latest']['ts']) + 1.0  # we add 1 just to make sure we start from the first message
        oldest = latest
        first_day = True

        while oldest > channel_info['channel']['created']:
            latest = oldest
            if first_day:
                # this is the datetime for the end of the day
                dt = datetime.fromtimestamp(latest).replace(hour=0, minute=0, second=0, microsecond=0)
                oldest = time.mktime(dt.timetuple())
                first_day = False
            else:
                oldest = latest - timedelta(days=1).total_seconds()

            self.log("Get messages for day: '{}'".format(datetime.fromtimestamp(oldest)))
            messages = self.get_channel_history_by_range(channel_id, latest, oldest)
            if not messages:
                self.log("  No messages. Maybe this day there were no messages, continue")
            else:
                self.save(self.payload['channel'], messages, oldest)
                self.log("  Messages saved!")

    def get_channel_history_by_range(self, channel_id, latest, oldest):
        all_messages = []
        history = {'has_more': True}
        while history['has_more']:
            history = self.slack.channels.history(channel_id, latest, oldest, inclusive=True, unreads=True,
                                                  count=1000).body
            if history['messages']:
                all_messages += history['messages']
                latest = float(history['messages'][-1]['ts'])
            else:
                break

        return all_messages

    def run(self):
        return getattr(self, self.settings.action)()


if __name__ == '__main__':
    SlackApi(parse_args()).run()
