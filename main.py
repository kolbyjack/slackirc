#!/usr/bin/env python

import irc
import json
import threading
import time
import yaml

from Queue import Queue
#from persistentdict import PersistentDict
from slackclient import SlackClient

#db = PersistentDict('slackirc.json')
with open('config.yml', 'r') as fp:
    config = yaml.load(fp)

class SlackThread(threading.Thread):
    def __init__(self, queue, config):
        super(SlackThread, self).__init__()
        self.daemon = True
        self.queue = queue
        self._config = config
        self.conn = None

    def run(self):
        try:
            print 'Connecting to slack'
            self.conn = SlackClient(self._config['token'])
            if not self.conn.rtm_connect():
                return

            self.parseLoginData(self.conn.server.login_data)

            print 'Connected to slack'
            self.conn.server.websocket.sock.setblocking(True)
            while True:
                for event in self.conn.rtm_read():
                    self.queue.put({'type': 'slack.event', 'data': event})
        except Exception as e:
            print 'SLACK RUNLOOP ERROR: %s' % e

        self.conn = None

    def parseLoginData(self, loginData):
        for user in loginData.get('users', []):
            if user.get('deleted', False):
                continue
            if user.get('is_bot', False):
                continue
            self.queue.put({'type': 'slack.join', 'data': {'id': user['id'], 'name': user['name']}})


class IrcThread(threading.Thread):
    def __init__(self, queue, config):
        super(IrcThread, self).__init__()
        self.daemon = True
        self.queue = queue
        self._config = config
        self.conn = irc.IrcClient(nick=self._config['nick'], password=self._config.get('password', None))

    def run(self):
        try:
            print 'Connecting to irc'
            host, port = self._config['server'].split(':')
            self.conn.connect(host, int(port))
            self.conn.join(self._config['channel'])
            print 'Connected to irc'
            for message in self.conn.messages():
                self.queue.put({'type': 'irc.message', 'data': message})
        except Exception as e:
            print 'IRC RUNLOOP ERROR: %s' % e


class SlackBot(threading.Thread):
    def __init__(self):
        super(SlackBot, self).__init__()
        self.daemon = True
        self.queue = Queue()
        self.slack = None
        self.irc = None

    def run(self):
        if self.slack is not None:
            return

        self.slack = SlackThread(self.queue, config['slack'])
        self.slack.start()

        self.irc = IrcThread(self.queue, config['irc'])
        self.irc.start()

        while True:
            event = self.queue.get()
            if event['type'] == 'slack.event':
                self.handleSlackEvent(event['data'])
            elif event['type'] == 'irc.message':
                self.handleIrcMessage(event['data'])
            self.queue.task_done()

    def handleSlackEvent(self, event):
        try:
            if event.get('type', None) != 'message' or 'subtype' in event:
                return

            user = self.slack.conn.server.users.find(event['user'])
            message = event['text']

            if event['channel'][0] != 'D':
                channel = self.slack.conn.server.channels.find(event['channel'])
                if channel.name == config['slack']['channel']:
                    irc_channel = config['irc']['channel']
                    if irc_channel[0] != '#':
                        irc_channel = '#%s' % irc_channel
                    self.irc.conn.send(irc_channel, message)
            else:
                pass # What to do with private messages?
        except Exception as e:
            print 'SLACK EVENT ERROR: %s' % e

    def handleIrcMessage(self, message):
        if message.command == 'PRIVMSG':
            if message.params[0][0] == '#':
                for channel in self.slack.conn.server.channels:
                    if channel.name == config['slack']['channel']:
                        if message.ctcp_command == 'ACTION':
                            text = '_%s %s_' % (message.prefix.name, message.params[1])
                        else:
                            text = '*%s:* %s' % (message.prefix.name, message.params[1])
                        channel.send_message(text)
                        break
            elif 'privmsg' in config['irc']:
                message = '@%s: %s' % (message.params[0], message.params[1])
                user = '@%s' % config['irc']['privmsg']
                print 'Sending %s to %s' % (message, user)
                message_json = {'type': 'message', 'channel': user, 'text': message}
                self.slack.conn.server.send_to_websocket(message_json)
        else:
            print message


if __name__ == '__main__':
    try:
        bot = SlackBot()
        bot.start()
        while True:
            time.sleep(24 * 60 * 60)
    except KeyboardInterrupt:
        pass

