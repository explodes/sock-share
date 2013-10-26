import json
import random
import weakref

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
        partner = self.get_paired_partner()
        if partner is not None:
            self.handleSpecialCommand('unpair', None, None)
        del WebShareServerProtocolPool[self.key]

    def handleSpecialCommand(self, command_name, args, echo):
        command = SpecialCommandRegistry[command_name]
        responses = command.perform_command(self, self.get_paired_partner(), args)
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

    def pair_with(self, other):
        other.paired_to = weakref.ref(self)
        self.paired_to = other

    def get_paired_partner(self):
        if isinstance(self.paired_to, weakref.ref):
            return self.paired_to()
        return self.paired_to

    def unpair(self):
        partner = self.get_paired_partner()
        if partner:
            partner.paired_to = None
        self.paired_to = None

def main(host, port):
    url = "ws://%s:%s" % (host, port)
    print 'Serving at: %s' % url
    factory = websocket.WebSocketServerFactory(url)
    factory.protocol = WebShareServerProtocol
    websocket.listenWS(factory)
    reactor.run()
