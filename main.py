#!/usr/bin/env python

import irc
import json
import time
import yaml

from slackclient import SlackClient

class Database(dict):
    def __init__(self, filename):
        self.filename = filename
        self.open(filename)

    def open(self, filename):
        self.clear()
        try:
            with open(filename, 'r') as fp:
                self.update(json.load(fp))
        except:
            pass

    def save(self):
        with open(self.filename, 'w') as fp:
            json.dump(self, fp)

    def __getitem__(self, key):
        return self.setdefault(key, {})

    def __setitem__(self, key, value):
        super(Database, self).__setitem__(key, value)
        self.save()

    def __delitem__(self, key):
        super(Database, self).__delitem__(key)
        self.save()

db = Database('slackirc.json')

with open('config.yml', 'r') as fp:
    config = yaml.load(fp)

slack = SlackClient(config['token'])
if slack.rtm_connect():
    while True:
        events = slack.rtm_read()

        for event in events:
            if event['type'] == 'message':
                if 'subtype' in event:
                    continue

                if 'text' not in event:
                    continue

                user = slack.server.users.find(event.get('user', None))
                if user is None:
                    continue

                channel = slack.server.channels.find(event.get('channel', None))
                if channel is None:
                    continue

                message = event['text']
                if channel.id[0] == 'D':
                    args = message.split(' ')
                    if len(args) == 3 and args[0] == 'set':
                        db['users'].setdefault(user.id, {})[args[1]] = args[2]
                        db.save()
                        if args[1] == 'nick':
                            # TODO: set user's nick in irc
                            pass
                        elif args[1] == 'password':
                            # TODO: identify with nickserv
                            pass
                    elif len(args) == 2 and args[0] == 'unset':
                        try:
                            del db['users'].setdefault(user.id, {})[args[1]]
                            db.save()
                        except KeyError:
                            pass
                    print '@%s: %s' % (user.name, message)
                else:
                    print '#%s/%s: %s' % (channel.name, user.name, message)

        if len(events) == 0:
            time.sleep(0.2)

#[
#  id : U0VTX1MQE tz : None name : ircbot real_name :,
#  id : U0R6LQN69 tz : America/Indiana/Indianapolis name : kolbyjack real_name :,
#  id : USLACKBOT tz : None name : slackbot real_name : slackbot
#],
#[
#  id : C0R6H9KKN name : general members : [u'U0R6LQN69', u'U0VTX1MQE'] server : username : ircbot domain : nginxirc webs
#  id : C0R6QJBQW name : random members : [] server : username : ircbot domain : nginxirc webs
#  id : D0VTU9SBE name : D0VTU9SBE members : [] server : username : ircbot domain : nginxirc webs
#  id : D0VU4DV0V name : D0VU4DV0V members : [] server : username : ircbot domain : nginxirc webs
#]


#{
#    u'type': u'presence_change',
#    u'user': u'U0VTX1MQE',
#    u'presence': u'active'
#}
#{
#    u'type': u'message',
#    u'text': u'<@U0VTX1MQE|ircbot> has joined the channel',
#    u'ts': u'1459179847.000006',
#    u'subtype': u'channel_join',
#    u'inviter': u'U0R6LQN69',
#    u'channel': u'C0R6H9KKN',
#    u'user': u'U0VTX1MQE'
#}
#{
#    u'type': u'message',
#    u'text': u'ping',
#    u'ts': u'1459179865.000007',
#    u'user': u'U0R6LQN69',
#    u'team': u'T0R6J9KH8',
#    u'channel': u'C0R6H9KKN'
#}

