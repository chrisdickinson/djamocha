from django.conf.urls.defaults import patterns, include, url
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from djamocha.context import get_current_runner
from djamocha.middleware import URLConfModule
import sys
import os

def parse_media(media):
    return {
        'css':getattr(media, 'css', {}),
        'js':getattr(media, 'js', [])
    }

class DjamochaMetaclass(type):
    def __new__(cls, name, bases, attrs):
        parents = [p for p in bases if isinstance(p, DjamochaMetaclass)]
        super_new = super(DjamochaMetaclass, cls).__new__
        if not parents:
            return super_new(cls, name, bases, attrs)

        media = attrs.pop('Media', attrs.pop('media', None))
        routes = attrs.pop('routes', None)

        if isinstance(media, type):
            media = parse_media(media)

        if routes is None:
            routes = patterns('')

        attrs['routes'] = routes
        attrs['media'] = media
        attrs['name'] = name
        attrs['js_dir'] = None

        klass = super_new(cls, name, bases, attrs)

        module_name = klass.__module__
        module = sys.modules[module_name]
        filename = module.__file__
        js_dir = os.path.join(os.path.dirname(os.path.abspath(filename)), 'js')
        klass.js_dir = js_dir

        runner = get_current_runner()
        runner.register(klass(runner))
        return klass 

class Test(object):
    __metaclass__ = DjamochaMetaclass

    def __init__(self, runner):
        self.runner = runner

    def view_main(self, request):
        return self.runner.view_suite(request, self)

    @csrf_exempt
    def view_xhr_pass(self, request):
        response = self.runner.report('pass', self, request)
        return response or HttpResponse('{"status":"ok"}')

    @csrf_exempt
    def view_xhr_fail(self, request):
        response = self.runner.report('fail', self, request)
        return response or HttpResponse('{"status":"ok"}')

    @csrf_exempt
    def view_xhr_done(self, request):
        response = self.runner.report('done', self, request)
        return response or HttpResponse('{"status":"ok"}')

    def get_urls(self):
        return patterns('',
            url(r'^media(?P<path>.*)$', 'django.views.static.serve', {'document_root':self.js_dir}),
            url(r'^xhr/pass/$', self.view_xhr_pass),
            url(r'^xhr/fail/$', self.view_xhr_fail),
            url(r'^xhr/done/$', self.view_xhr_done),
            url(r'^$', self.view_main),
            url(r'^', include(isinstance(self.routes, list) and URLConfModule(self.routes) or include(self.routes))),
        )
