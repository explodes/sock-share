import json
import random
import threading

from autobahn import websocket
from twisted.internet import reactor

from webshare.share.commands import enums
from webshare.share.commands.base import CommandRegistry
from webshare.share.commands.special import SpecialCommandRegistry


class _WebShareServerProtocolPool(dict):
    pass


WebShareServerProtocolPool = _WebShareServerProtocolPool()


def gen_key():
    while True:
        key = '%x' % random.getrandbits(32)
        if key not in WebShareServerProtocolPool:
            return key


class WebShareServerProtocol(websocket.WebSocketServerProtocol):
    def __init__(self, *args, **kwargs):
        self.key = gen_key()
        self.paired_to = None
        WebShareServerProtocolPool[self.key] = self
        print 'Client %s created' % self.key

    def onMessage(self, message, is_binary):
        if is_binary:
            return self.onCommandError(enums.ERROR_INVALID_REQUEST)

        echo = None

        try:
            request = json.loads(message)
            command_name = request['command']
            args = request.get('body')
            echo = request.get('echo')
        except KeyError as error:
            return self.onCommandError(enums.ERROR_INCOMPLETE_FORMAT, echo, error=error)
        except Exception as error:
            return self.onCommandError(enums.ERROR_INVALID_FORMAT, echo, error=error)

        if command_name in SpecialCommandRegistry:
            self.handleSpecialCommand(command_name, args, echo)
        elif command_name in CommandRegistry:
            self.handleCommand(command_name, args, echo)
        else:
            return self.onCommandError(enums.ERROR_UNKNOWN_COMMAND, echo)

    def connectionLost(self, reason):
        print 'Client %s lost' % self.key
        if self.paired_to is not None:
            print 'Unpairing with Client %s' % self.paired_to.key
            self.handleSpecialCommand('unpair', None, None)
        del WebShareServerProtocolPool[self.key]

    def handleSpecialCommand(self, command_name, args, echo):
        command = SpecialCommandRegistry[command_name]
        responses = command.perform_command(self, self.paired_to, args)
        for target, response in responses:
            self.sendResponse(target, command_name, response, echo)

    def handleCommand(self, command_name, args, echo):
        command = CommandRegistry[command_name]
        response = command.perform_command(args)
        self.sendResponse(self, command_name, response, echo)

    def sendResponse(self, target, command_name, response, echo):
        response['echo'] = echo
        response['command'] = command_name
        response_str = json.dumps(response)
        target.sendMessage(response_str)

    def onCommandError(self, message, echo, error=None):
        if error:
            print 'Error:', type(error), error
        self.handleSpecialCommand('error', {'error': message}, echo)


def main(host, port):
    url = "ws://%s:%s" % (host, port)
    print 'Serving at: %s' % url
    factory = websocket.WebSocketServerFactory(url)
    factory.protocol = WebShareServerProtocol
    websocket.listenWS(factory)
    reactor.run()
