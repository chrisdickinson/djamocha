import sys
from StringIO import StringIO

original_stderr = sys.stderr
original_stdout = sys.stdout

sys.stderr = StringIO()
sys.stdout = StringIO()

from django.core.management.base import BaseCommand
from optparse import make_option
from djamocha.runner import CLIRunner

from django.test.simple import build_suite
from django.db.models import get_apps

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),
        make_option('--addrport', action='store', dest='addrport',
            type='string', default='',
            help='port number or ipaddr:port to run the server on'),
        make_option('--ipv6', '-6', action='store_true', dest='use_ipv6', default=False,
            help='Tells Django to use a IPv6 address.'),
        make_option('--open', '-o', action='store_true', dest='open_url', default=False,
            help='Will attempt to open the URL in your browser to start the test.'),
    )
    help = 'Runs a development server with data from the given fixture(s).'
    args = '[fixture ...]'

    requires_model_validation = False

    def handle(self, *fixture_labels, **options):
        from django.core.management import call_command
        from django.db import connection
        from django.conf import settings

        settings.MIDDLEWARE_CLASSES = list(settings.MIDDLEWARE_CLASSES) + ['djamocha.middleware.DjamochaTestMiddleware']

        verbosity = int(options.get('verbosity'))
        interactive = options.get('interactive')
        addrport = options.get('addrport')

        # Create a test database.
        db_name = connection.creation.create_test_db(verbosity=verbosity, autoclobber=not interactive)

        # Import the fixture data into the test database.
        call_command('loaddata', *fixture_labels, **{'verbosity': verbosity})

        runner = CLIRunner(
            stderr=original_stderr,
            stdout=original_stdout
        )

        for app in get_apps():
            build_suite(app)

        # Run the development server. Turn off auto-reloading because it causes
        # a strange error -- it causes this handle() method to be called
        # multiple times.
        shutdown_message = '\nServer stopped.\nNote that the test database, %r, has not been deleted. You can explore it on your own.' % db_name
        call_command('runserver', addrport=addrport, shutdown_message=shutdown_message, use_reloader=False, use_ipv6=options['use_ipv6'])

