from optparse import make_option

from django.core.management import BaseCommand

from webshare.share import server


class Command(BaseCommand):

    args = '[--host=xxx.xxx.xxx] [--port=xxxx]'
    help = 'Start up the Share websockets server.'

    option_list = BaseCommand.option_list + (
        make_option('--host', dest='host', default='127.0.0.1', help='Bind to this IP address'),
        make_option('--port', dest='port', default='9000', help='Bind to this port')
    )

    def handle(self, *args, **options):

        host = options['host']
        port = options['port']
        server.main(host, port)
