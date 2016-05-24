#!/usr/bin/env python

import sys
import socket

class Prefix(object):
    def __init__(self, prefix=''):
        self.host = None
        if '!' in prefix:
            self.name, prefix = prefix.split('!', 1)
            if '@' in prefix:
                self.user, self.host = prefix.split('@', 1)
            else:
                self.user = prefix
        else:
            self.name = prefix

    def __str__(self):
        if self.host is None:
            return self.name
        else:
            return '%s@%s' % (self.name, self.host)

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
        return "{prefix: '%s'; command: '%s'; params: '%s'}" % (self.prefix, self.command, self.params)

class IrcClient(object):
    def __init__(self, nick=None, ident=None, realname=None, password=None):
        self.nick = nick
        self.password = password
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
        if self.password is not None:
            self.send('nickserv', 'identify %s' % self.password)

        ident = self.nick if self.ident is None else self.ident
        realname = self.nick if self.realname is None else self.realname

        self.sock.send('USER %s 0 * :%s\r\n' % (ident, realname))

    def close(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def join(self, channel):
        if channel[0] != '#':
            channel = '#%s' % channel
        self.sock.send('JOIN %s\r\n' % channel)

    def send(self, channel, message):
        self.sock.send('PRIVMSG %s :%s\r\n' % (channel, message))

    def read(self):
        while len(self._messages) == 0:
            self._readbuffer += self.sock.recv(1024)
            temp = self._readbuffer.split('\n')
            self._readbuffer = temp.pop()

            self._messages.extend([Message(line) for line in temp])

            while len(self._messages) > 0 and self._messages[0].command == 'PING':
                ping = self._messages.pop(0)
                if len(ping.params) > 1:
                    cookie = ping.params[1]
                else:
                    cookie = self.nick
                self.sock.send('PONG %s\r\n' % cookie)

        return self._messages.pop(0)

    def messages(self):
        while True:
            yield self.read()

if __name__ == '__main__':
    client = IrcClient(nick='kolbyslack')
    client.connect('chat.freenode.net', 6667)
    client.join('#kolbyslack')
    for message in client.messages():
        print message
        if message.command == 'PRIVMSG':
            if message.params[0][0] == '#':
                print '%s <%s> %s' % (message.params[0], message.prefix.name, message.params[1])
            else:
                print '<%s> %s' % (message.params[0], message.params[1])

