#!/usr/bin/env python

import irc
import json
import time
import yaml

from persistentdict import PersistentDict
from slackclient import SlackClient

db = PersistentDict('slackirc.json')

class Bot(object):
    def __init__(self):
        with open('config.yml', 'r') as fp:
            self.config = yaml.load(fp)
        self.slack = None
        self.irc = {}

    def run(self):
        if self.slack is None:
            self.openSlackConnection()

        for user in db['users']:
            if 'nick' in user and user not in self.irc:
                openIrcConnection(self, user)

    def openSlackConnection(self):
        try:
            self.slack = SlackClient(self.config['token'])
            if not self.slack.rtm_connect():
                return

            self.slack.server.websocket.sock.setblocking(True)
            while True:
                for event in self.slack.rtm_read():
                    self.handleSlackEvent(event)
        except Exception as e:
            print 'ERROR: %s' % e

        self.slack = None

    def handleSlackEvent(self, event):
        try:
            if event['type'] != 'message' or 'subtype' in event:
                return

            user = self.slack.server.users.find(event['user'])
            message = event['text']

            if event['channel'][0] == 'D':
                self.handleSlackPrivateMessage(user, message)
            else:
                channel = self.slack.server.channels.find(event['channel'])
                self.handleSlackChannelMessage(channel, user, message)
        except Exception as e:
            print 'ERROR: %s' % e

    def handleSlackChannelMessage(self, channel, user, message):
        print '#%s/%s: %s' % (channel.name, user.name, message)

    def handleSlackPrivateMessage(self, user, message):
        try:
            args = message.split(' ')
            if args[0] == 'sync':
                db['channels'].setdefault(args[1], {})['sync'] = True
                db.save()

            elif args[0] == 'set':
                db['users'].setdefault(user.id, {})[args[1]] = args[2]
                db.save()

                if args[1] == 'nick':
                    print "TODO: set user's nick in irc"
                elif args[1] == 'password':
                    print "TODO: identify with nickserv"

            elif args[0] == 'unset':
                del db['users'].setdefault(user.id, {})[args[1]]
                db.save()
        except Exception as e:
            pass

        print '@%s: %s' % (user.name, message)

    def openIrcConnection(self, user):
        self.irc[user] = 

if __name__ == '__main__':
    Bot().run()

