from djamocha.client import Client
from djamocha.context import set_current_runner
from djamocha.middleware import URLConfModule
from django.conf import settings
from django.conf.urls.defaults import patterns, include, url
from django.http import HttpResponse, HttpResponseRedirect
from django.template import Template, Context, RequestContext
from django.template.loader import select_template
from django.utils import simplejson
import os
import sys

DJAMOCHA_MEDIA_URL = getattr(settings, 'DJAMOCHA_MEDIA_URL', '/djamocha_media/')

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets')

JQUERY = open(os.path.join(base, 'jquery.min.js'), 'r').read()
MOCHA_CSS = open(os.path.join(base, 'mocha.css'), 'r').read()
MOCHA_JS = open(os.path.join(base, 'mocha.js'), 'r').read()
MOCHA_ASSERT = open(os.path.join(base, 'assert.js'), 'r').read() 

class Runner(object):
    def __init__(self, stdout=None, stderr=None, cookie_name=settings.SESSION_COOKIE_NAME):
        self.clients = {}
        self.tests = []
        self.failures = [] 
        self.cookie_name = cookie_name
        self.stdout = stdout
        self.stderr = stderr
        set_current_runner(self)

    def register(self, suite):
        self.tests.append(suite)

    def attach_client(self, request):
        uuid = request.COOKIES.get(self.cookie_name)
        self.clients[uuid] = Client(uuid, request)
        return self.clients[uuid]

    def get_client_from_request(self, request):
        uuid = request.COOKIES.get(self.cookie_name)
        return self.clients.get(uuid, None)

    def report(self, name, suite, data):
        responder = getattr(self, 'respond_%s' % name, lambda *a : None)
        return responder(suite, data) 

    def view_main(self, request):
        client = self.get_client_from_request(request) or self.attach_client(request)

        if len(client.tests):
            return self.view_suite(request, client.tests[-1])

        client.set_tests(self.tests[:])

        if not len(client.tests):
            return self.view_done(request)

        return HttpResponseRedirect('/')

    def view_done(self, request):
        return HttpResponse("<h1>ALL DONE</h1>")

    def view_suite(self, request, suite):
        client = self.get_client_from_request(request)

        template = getattr(suite, 'template', None)
        if template:
            template = select_template([template])
        else:
            template = Template(BASE_TEMPLATE)

        html = template.render(RequestContext(request, {
            'client':client,
            'suite':suite
        }))
        return HttpResponse(html)

    def view_idle(self, request):
        if request.META.get('HTTP_X_REQUESTED_WITH', None) == 'Ajax':
            return HttpResponse('ready')

        return HttpResponse("""
            <p>idling...</p>
            <script>
                var popup
                  , xhr

                setInterval(function() {
                  if(popup && popup.FINISHED) {
                    xhr = new XMLHttpRequest
                    xhr.open('GET', '/done/', false)
                    try { xhr.send(null) } catch(err) { }

                    popup.close()
                    popup = null
                  } else if(popup) {
                    return
                  } else { 
                    xhr = new XMLHttpRequest
                    xhr.open('GET', '/idle/', false)
                    xhr.setRequestHeader('X-Requested-With', 'Ajax')
                    xhr.send(null)
                    if(xhr.responseText === 'ready') {
                      popup = open('/')
                      popup.blur()
                      window.focus()
                    }
                  }
                }, 500)
            </script>
        """)

    def respond_fail(self, suite, request):
        self.failures.append(request.POST.get('error'))

    def respond_pass(self, suite, request):
        pass

    def respond_done(self, suite, request):
        client = self.get_client_from_request(request)
        next = client.next_test()
        return HttpResponse(simplejson.dumps({
            'location':next
        }))

    def get_urls(self, request):
        client = self.get_client_from_request(request) or self.attach_client(request)

        p = patterns('django.views.static',
            (r'^'+DJAMOCHA_MEDIA_URL[1:-1]+'/jquery.min.js', lambda r : HttpResponse(JQUERY)),
            (r'^'+DJAMOCHA_MEDIA_URL[1:-1]+'/mocha.css', lambda r : HttpResponse(MOCHA_CSS)),
            (r'^'+DJAMOCHA_MEDIA_URL[1:-1]+'/mocha.js', lambda r : HttpResponse(MOCHA_JS)),
            (r'^'+DJAMOCHA_MEDIA_URL[1:-1]+'/assert.js', lambda r : HttpResponse(MOCHA_ASSERT)),
            (r'^'+DJAMOCHA_MEDIA_URL[1:-1]+'(?P<path>.*)$', 'serve',
            {'document_root': settings.MEDIA_ROOT}),
        )

        p += patterns('',
            url('^$', self.view_main),
            url('^idle/$', self.view_idle),
            url('^done/$', self.view_done),
        )

        if len(client.tests):
            p += patterns('', ('^', include(URLConfModule(client.tests[-1].get_urls()))))

        return p

class CLIRunner(Runner):
    def respond_fail(self, suite, data):
        self.stderr.write('F')
        return super(CLIRunner, self).respond_fail(suite, data)

    def respond_pass(self, suite, data):
        self.stderr.write('.')
        return super(CLIRunner, self).respond_pass(suite, data)

    def view_done(self, request):
        # need to use os._exit because sys.exit doesn't work in a thread.

        print >>self.stderr, "\n\nRan %d tests, %d failures" % (len(self.tests), len(self.failures))

        print >>self.stderr, "\n\n"
        for failure in self.failures:
            print >>self.stderr, failure, "\n"

        os._exit(len(self.failures))


BOOT_MOCHA = """
;(function(){
  var suite = new mocha.Suite
    , utils = mocha.utils
    , Reporter = mocha.reporters.HTML

  mocha.setup = function(ui){
    ui = mocha.interfaces[ui];
    if (!ui) throw new Error('invalid mocha interface "' + ui + '"');
    ui(suite);
    suite.emit('pre-require', window);
  };

  mocha.run = function(){
    suite.emit('run');
    var runner = new mocha.Runner(suite);
    var reporter = new Reporter(runner);

    runner.on('end', console.log.bind(console, "END"))
    runner.on('test end', console.log.bind(console, "TEST END"))
    runner.on('pass', console.log.bind(console, 'PASS'))
    runner.on('fail', console.log.bind(console, 'FAIL'))
   
    runner.on('pass', function() {
        $.post('/xhr/pass/', {})
    })

    runner.on('fail', function(test, err) {
        $.post('/xhr/fail/', {'error':err ? err.stack || ''+err : 'ERROR'})
    })

    runner.on('end', function() {
        $.post('/xhr/done/', {}, function(resp) {
            resp = JSON.parse(resp)
            if(resp.location === '/done/') {
              window.FINISHED = true
            }
        })
    })
 
    return runner.run();
  };
})();
"""

BASE_TEMPLATE = """
<!doctype html>
<meta charset="utf8" />
<title> djamocha </title>
<link rel="stylesheet" href="%(djamochamedia)smocha.css" />
<script src="%(djamochamedia)sjquery.min.js"></script>
<script src="%(djamochamedia)smocha.js"></script>
<script>
    %(boot)s
</script> 

<script src="%(djamochamedia)sassert.js"></script>
{%% for script in suite.media.js %%}
    <script type="text/javascript" src="%(djamochamedia)s{{ script }}"></script>
{%% endfor %%}

<script>mocha.setup('tdd')</script>

{%% for script in suite.tests %%}
    <script type="text/javascript" src="/media/{{ script }}"></script>
{%% endfor %%}

<script>
  onload = function(){
    mocha
      .run()
      .globals(['assert'])
  };
</script>

<div id="mocha"></div>
""" % {'djamochamedia':DJAMOCHA_MEDIA_URL, 'boot':BOOT_MOCHA}
