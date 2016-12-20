#!/usr/bin/env python

from __future__ import print_function, unicode_literals

import argparse
import codecs
import json
import os
import time
from datetime import timedelta, datetime
from pprint import pprint
from slacker import Slacker
import requests
import shutil
import subprocess

SLACK_ACTIONS = ['post_message', 'pull_messages', 'pull_users']


def parse_args():
    """
    Parse arguments for input params
    """

    parser = argparse.ArgumentParser(prog="Jenkins Scheduler Generator")

    parser.add_argument('-a', '--action', required=True, choices=SLACK_ACTIONS,
                        help='Slack API action to perform')
    parser.add_argument('-tf', '--token_file', required=False, default='/opt/secrets/slack/slack-token',
                        help='Path to slack API token')
    parser.add_argument('-p', '--payload', required=True, help='Slack API payload for specific action')
    parser.add_argument('-o', '--output_path', required=False, default='/opt/s3/slack',
                        help='Specify path to save output data')
    parser.add_argument('-d', '--debug', default=False, action='store_true', help="Enable debug mode")

    return parser.parse_args()


class Base(object):
    def log(self, msg):
        print(msg)

    def logp(self, msg):
        pprint(msg)

    pass


class SlackApi(Base):
    NAME = 'slack'

    def __init__(self, settings):
        self.settings = settings
        self.token = self.get_token_from_file()
        self.slack = Slacker(self.token)
        self.payload = self.validate_payload()
        self.request = self.init_request()
        self._team_domain = None

    def get_token_from_file(self):
        """Load token from file"""

        with open(self.settings.token_file, 'r') as f:
            token = f.read().strip()

        return token

    def init_request(self):
        """Init requests with auth headers"""

        # we need to pass auth if we want to make request to
        headers = {'Authorization': 'Bearer ' + self.token}
        request = requests.Session()
        request.headers = headers

        return request

    def validate_payload(self):
        """Make sure that payload is json formated"""

        return json.loads(self.settings.payload)

    def make_dirs(self, *folders):
        """Create dirs if not exists"""

        for p in [self.settings.output_path, os.path.join(self.settings.output_path, *folders)]:
            if not os.path.exists(p):
                os.makedirs(p)

    @property
    def team_domain(self):
        if self._team_domain:
            return self._team_domain

        self._team_domain = self.slack.team.info().body['team']['domain']

        return self._team_domain

    def s3_sync(self, folder_name, action_name=None):
        """Command to sync all the files to S3 bucket"""

        s3_bucket = 's3://{bucket_name}/plugins/{plugin_name}/{team_domain}'

        if action_name:
            s3_bucket += '/{action_name}'

        s3_bucket += '/{folder_name}'

        s3_bucket = s3_bucket.format(
            bucket_name=self.payload['s3_bucket'],
            plugin_name=self.NAME,
            team_domain=self.team_domain,
            action_name=action_name,
            folder_name=folder_name
        )
        cmd = 'aws s3 sync {local_path} {s3_bucket}'.format(
            local_path=os.path.join(self.settings.output_path, folder_name),
            s3_bucket=s3_bucket
        )
        self.log("Run cmd: {}".format(cmd))

        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        out, err = process.communicate()

        if err:
            self.log("    S3 SYNC ERROR: {}".format(err))
        else:
            self.log("    S3 SYNC OK")
            self.log(out)

    def save_json(self, file_path, data):
        with codecs.open(file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(data, indent=4, ensure_ascii=False))

    def save_messages(self, channel_name, messages_data, timestamp):
        """Save messages for a day into a file"""

        dt = datetime.fromtimestamp(timestamp)

        file_format = '{team_domain}_{channel_name}_{date}.json'.format(
            team_domain=self.team_domain,
            channel_name=channel_name,
            date=dt.strftime("%Y-%m-%d")
        )
        date_in_folder = dt.strftime("%Y-%m")
        self.make_dirs(channel_name, date_in_folder, 'messages')

        file_path = os.path.join(self.settings.output_path, channel_name, date_in_folder, 'messages', file_format)

        self.save_json(file_path, messages_data)

        return file_path

    def download_file(self, url, timestamp, channel_name):
        """Download file url and appends it's datetime to it's name"""

        dt = datetime.fromtimestamp(timestamp)

        response = self.request.get(url, stream=True)

        file_format = '{team_domain}_{channel_name}_{date}_{file_name}.json'.format(
            team_domain=self.team_domain,
            channel_name=channel_name,
            date=dt.strftime("%Y-%m-%d"),
            file_name=os.path.basename(url)
        )

        date_in_folder = dt.strftime("%Y-%m")
        self.make_dirs(channel_name, date_in_folder, 'binaries')

        file_path = os.path.join(self.settings.output_path, channel_name, date_in_folder, 'binaries', file_format)

        with open(file_path, 'wb') as out_file:
            shutil.copyfileobj(response.raw, out_file)
        del response

        return file_path

    def save_slack_files(self, channel_name, messages_data):
        """
        Process all the messages and download the files
        """

        for message in messages_data:
            if 'file' in message:
                self.log("Download file: {}".format(message['file']['url_private_download']))
                self.download_file(message['file']['url_private_download'], message['file']['timestamp'], channel_name)

    def get_channel_history_by_range(self, channel_id, latest, oldest, count=1000):
        """
        Get all messages from a channel from specific date ranges
        in backward mode - first messages  are the latest one
        """

        all_messages = []
        history = {'has_more': True}
        while history['has_more']:
            history = self.slack.channels.history(channel_id, latest, oldest, inclusive=True, unreads=True,
                                                  count=count).body
            if history['messages']:
                all_messages += history['messages']
                latest = float(history['messages'][-1]['ts'])
            else:
                break

        return all_messages

    def post_message(self):
        """Post a message to a channel"""

        r = self.slack.chat.post_message(self.payload['channel'], self.payload['text'], **self.payload.get('args', {}))
        self.log(r.body)
        return r

    def pull_messages(self):
        """Pull all messages from from a channel and sore in files by days"""

        if self.payload.get('all_channels', False):
            channels = [c['name'] for c in self.slack.channels.list().body['channels']]
        else:
            channels = map(lambda s: s.strip(), self.payload['channels'].split(','))

        for channel_name in channels:
            self.log("Get history of channel: {}".format(channel_name))
            channel_id = self.slack.channels.get_channel_id(channel_name)
            channel_info = self.slack.channels.info(channel_id).body

            if 'latest' not in channel_info['channel']:
                self.log("Seems that there are no messages in channel: '{}'. Skip.".format(channel_name))
                continue

            latest = float(
                channel_info['channel']['latest'][
                    'ts']) + 1.0  # we add 1 just to make sure we start from the first message
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
                    self.log("  No messages. Maybe on this day there were no messages?, continue")
                else:
                    self.save_messages(channel_name, messages, oldest)
                    self.log("  Messages saved!")
                    self.save_slack_files(channel_name, messages)

            # after all messages were processed, we can sync the result to s3
            self.s3_sync(channel_name, 'messages')

    def pull_users(self):
        file_name = 'users'

        file_format = '{team_domain}_{file_name}.json'.format(
            team_domain=self.team_domain,
            file_name=file_name
        )
        self.make_dirs(file_name)

        file_path = os.path.join(self.settings.output_path, file_name, file_format)
        users = self.slack.users.list(presence=True).body['members']

        self.save_json(file_path, users)

        self.s3_sync(file_name)

    def run(self):
        """Entry point"""

        return getattr(self, self.settings.action)()


if __name__ == '__main__':
    SlackApi(parse_args()).run()
