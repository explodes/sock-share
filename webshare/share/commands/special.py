import weakref

from webshare.share.commands import enums


def get_pool():
    from webshare.share.server import WebShareServerProtocolPool

    return WebShareServerProtocolPool


class _SpecialCommandRegistry(dict):
    pass


SpecialCommandRegistry = _SpecialCommandRegistry()


def special_command(command_name):
    def special_command(klass):
        SpecialCommandRegistry[command_name] = klass()
        # Return klass un-phased
        return klass

        # return decorator

    return special_command


class SpecialCommand(object):
    def perform_command(self, client, paired_to, arguments):
        return self.respond_success()

    def respond_fail(self, client, body=None, code=enums.CODE_FAIL):
        return self.create_response(client, enums.STATUS_FAIL, body=body, code=code)

    def respond_success(self, client, body=None, code=enums.CODE_SUCCESS):
        return self.create_response(client, enums.STATUS_OK, body=body, code=code)

    def create_response(self, client, ok, code, body):
        response = {
            'ok': ok,
            'code': code,
            'body': body,
        }
        return client, response


@special_command('pair')
class Pair(SpecialCommand):
    def perform_command(self, client, paired_to, arguments):
        if paired_to is not None:
            yield self.respond_fail(client, code=enums.CODE_ALREADY_PAIRED)
            return

        if client.paired_to is not None:
            yield self.respond_fail(client, code=enums.CODE_ALREADY_PAIRED)
            return

        if not isinstance(arguments, dict):
            yield self.respond_fail(client, code=enums.CODE_INVALID_ARGUMENTS)
            return

        target_key = arguments.get('target')

        if not target_key:
            yield self.respond_fail(client, code=enums.CODE_INVALID_KEY)
            return

        target = get_pool().get(target_key)
        if target is None:
            yield self.respond_fail(client, code=enums.CODE_TARGET_NOT_FOUND)
            return

        client.paired_to = target
        target.paired_to = weakref.ref(client)

        print 'Client %s paired with client %s' % (client.key, target.key)

        yield self.respond_success(client, code=enums.CODE_SUCCESS, body={'with': target_key})
        yield self.respond_success(target, code=enums.CODE_SUCCESS, body={'with': client.key})


@special_command('unpair')
class Unpair(SpecialCommand):
    def perform_command(self, client, paired_to, arguments):
        if paired_to is None:
            yield self.respond_fail(client, code=enums.CODE_NOT_PAIRED)
            return

        client.paired_to = None
        paired_to.paired_to = None

        print 'Client %s unpaired with client %s' % (client.key, paired_to.key)

        yield self.respond_success(client, code=enums.CODE_SUCCESS, body={'with': paired_to.key})
        yield self.respond_success(paired_to, code=enums.CODE_SUCCESS, body={'with': client.key})


@special_command('relay')
class Relay(SpecialCommand):
    def perform_command(self, client, paired_to, arguments):
        if paired_to is None:
            yield self.respond_fail(client, code=enums.CODE_NOT_PAIRED)
            return

        print 'Client %s will relay to client %s: %s' % (client.key, paired_to.key, arguments)

        yield self.respond_success(paired_to, code=enums.CODE_SUCCESS, body=arguments)


@special_command('key')
class Key(SpecialCommand):
    def perform_command(self, client, paired_to, arguments):
        print 'Client %s requesting key' % client.key
        yield self.respond_success(client, code=enums.CODE_SUCCESS, body={'key': client.key})


@special_command('error')
class Error(SpecialCommand):
    def perform_command(self, client, paired_to, arguments):
        error = arguments['error']
        yield self.respond_fail(client, code=enums.CODE_COMMAND_ERROR, body={'error': error})