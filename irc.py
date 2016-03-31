#!/usr/bin/env python

import sys
import socket

HOST = 'chat.freenode.net'
PORT = 6667
NICK = 'kolbyslack'
IDENT = 'kolbyslackbot'
REALNAME = 'kolbyslackbot'
readbuffer = ''

s = socket.socket()
s.connect((HOST, PORT))
s.send('NICK %s\r\n' % NICK)
s.send('USER %s %s bla :%s\r\n' % (IDENT, HOST, REALNAME))
s.send('JOIN %s\r\r' % '#kolbyslack-test')

class Prefix(object):
    def __init__(self, prefix=''):
        if '!' in prefix:
            self.name, prefix = prefix.split('!', 1)
            if '@' in prefix:
                self.user, self.host = prefix.split('@', 1)
            else:
                self.user = prefix
        else:
            self.name = prefix

class Message(object):
    def __init__(self, line):
        self.prefix = Prefix()

        line = line.strip()
        if line[0] == ':':
            prefix, line = line.split(' ', 1)
            self.prefix = Prefix(prefix[1:])

        if ' :' in line:
            line, trailing = line.split(' :', 1)
            self.params = line.split()
            self.params.append(trailing)
        else:
            self.params = line.split()

        self.command = self.params.pop(0)

    def __str__(self):
        return "{prefix: '%s'; command: '%s'; params: '%s'}" % (self.prefix.name, self.command, self.params)

while True:
    readbuffer += s.recv(1024)
    temp = readbuffer.split('\n')
    readbuffer = temp.pop()

    for line in temp:
        message = Message(line)
        print message
        if message.command == 'PING':
            s.send('PONG %s\r\n' % args[1])
        elif message.command == 'PRIVMSG':
            if message.params[0][0] == '#':
                print '%s <%s> %s' % (message.params[0], message.prefix.name, message.params[1])
            else:
                print '<%s> %s' % (message.params[0], message.params[1])

