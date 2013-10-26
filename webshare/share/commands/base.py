from webshare.share.commands import enums


class _CommandRegistry(dict):
    pass

CommandRegistry = _CommandRegistry()

def command(command_name):
    def command(klass):
        CommandRegistry[command_name] = klass()
        # Return klass un-phased
        return klass
    # return decorator
    return command

class BaseCommand(object):

    def perform_command(self, arguments):
        return self.respond_success()

    def respond_fail(self, body=None, code=enums.CODE_FAIL):
        return self.create_response(enums.STATUS_FAIL, body=body, code=code)

    def respond_success(self, body=None, code=enums.CODE_SUCCESS):
        return self.create_response(enums.STATUS_OK, body=body, code=code)

    def create_response(self, ok, code, body):
        response = {
            'ok': ok,
            'code': code,
            'body': body,
        }
        return response

