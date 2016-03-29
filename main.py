#!/usr/bin/env python

import irc
import time
import yaml

from slackclient import SlackClient

with open('config.yml', 'r') as fp:
    config = yaml.load(fp)

slack = SlackClient(config['token'])
if slack.rtm_connect():
    while True:
        events = slack.rtm_read()

        for event in events:
            if event['type'] == 'message':
                if 'subtype' not in event:
                    user = slack.server.users.find(event['user'])
                    print '%s: %s' % (user.name, event['text'])
                else:
                    print event
            elif event['type'] == 'presence_change':
                # TODO: Set IRC away status
                pass
            elif event['type'] not in ('reconnect_url', 'hello', 'user_typing'):
                print event

        if len(events) == 0:
            time.sleep(0.5)

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

