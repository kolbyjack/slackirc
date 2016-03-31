#!/usr/bin/env python

import sys
import socket

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

class IrcClient(object):
    def __init__(self, nick=None, ident=None, realname=None):
        self.nick = nick
        self.ident = ident
        self.realname = realname
        self.sock = None
        self._messages = []
        self._readbuffer = ''

    def connect(self, host, port):
        if self.sock is not None:
            raise Exception('Already connected')

        if self.nick is None:
            raise Exception('Nickname not set')

        self.sock = socket.socket()
        self.sock.connect((host, port))
        self.sock.send('NICK %s\r\n' % self.nick)

        ident = self.nick if self.ident is None else self.ident
        realname = self.nick if self.realname is None else self.realname

        self.sock.send('USER %s 0 * :%s\r\n' % (ident, realname))

    def join(self, channel):
        self.sock.send('JOIN %s\r\n' % channel)

    def send(self, channel, message):
        self.sock.send('PRIVMSG %s :%s\r\n' % channel, message)

    def read(self):
        while len(self._messages) == 0:
            self._readbuffer += self.sock.recv(1024)
            temp = self._readbuffer.split('\n')
            self._readbuffer = temp.pop()

            self._messages.extend([Message(line) for line in temp])

        return self._messages.pop(0)

    def messages(self):
        while True:
            yield self.read()

client = IrcClient(nick='kolbyslack')
client.connect('chat.freenode.net', 6667)
for message in client.messages():
    print message
    if message.command == 'PING':
        s.send('PONG %s\r\n' % args[1])
    elif message.command == 'PRIVMSG':
        if message.params[0][0] == '#':
            print '%s <%s> %s' % (message.params[0], message.prefix.name, message.params[1])
        else:
            print '<%s> %s' % (message.params[0], message.params[1])

