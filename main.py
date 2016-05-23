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
    def __init__(self, queue):
        super(SlackThread, self).__init__()
        self.daemon = True
        self.queue = queue
        self.conn = None

    def run(self):
        try:
            self.conn = SlackClient(config['slack']['token'])
            if not self.conn.rtm_connect():
                return

            self.parseLoginData(self.conn.server.login_data)

            self.conn.server.websocket.sock.setblocking(True)
            while True:
                for event in self.conn.rtm_read():
                    print event
                    self.queue.put({'type': 'slack.event', 'data': event})
        except Exception as e:
            print 'ERROR: %s' % e

        self.conn = None

    def parseLoginData(self, loginData):
        for user in loginData.get('users', []):
            if user.get('deleted', False):
                continue
            if user.get('is_bot', False):
                continue
            self.queue.put({'type': 'slack.join', 'data': {'id': user['id'], 'name': user['name']}})


class IrcThread(threading.Thread):
    def __init__(self, nick, queue):
        super(IrcThread, self).__init__()
        self.daemon = True
        self.nick = nick
        self.queue = queue
        self.conn = irc.IrcClient(nick=nick)

    def run(self):
        try:
            host, port = config['irc']['server'].split(':')
            self.conn.connect(host, int(port))
            self.conn.join(config['irc']['channel'])
            for message in self.conn.messages():
                print message
                self.queue.put({'type': 'irc.message', 'data': message})
        except Exception as e:
            print 'ERROR: %s' % e


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

        self.slack = SlackThread(self.queue)
        self.slack.start()

        self.irc = IrcThread(config['irc']['nick'], self.queue)
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
            if event['type'] != 'message' or 'subtype' in event:
                return

            user = self.slack.conn.server.users.find(event['user'])
            message = event['text']

            if event['channel'][0] != 'D':
                channel = self.slack.conn.server.channels.find(event['channel'])
                print 'slack #%s/%s: %s' % (channel.name, user.name, message)
                if channel.name == config['slack']['channel']:
                    self.irc.conn.send(config['irc']['channel'], message)
            else:
                pass # What to do with private messages?
        except Exception as e:
            print 'ERROR: %s' % e

    def handleIrcMessage(self, message):
        print message
        if message.command == 'PRIVMSG':
            if message.params[0][0] == '#':
                for channel in self.slack.conn.server.channels:
                    if channel.name == config['slack']['channel']:
                        channel.send_message('%s: %s' % (message.prefix.name, message.params[1]))
                        break
            else:
                print '@%s: %s' % (message.params[0], message.params[1])


if __name__ == '__main__':
    try:
        bot = SlackBot()
        bot.start()
        while True:
            time.sleep(24 * 60 * 60)
    except KeyboardInterrupt:
        pass

