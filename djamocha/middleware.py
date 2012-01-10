from djamocha.context import get_current_runner

class URLConfModule(object):
    def __init__(self, urlpatterns):
        self.urlpatterns = urlpatterns
    
    def __len__(self):
        return len(self.urlpatterns)
    
    def __iter__(self):
        return iter(self.urlpatterns)

class DjamochaTestMiddleware(object):
    def process_request(self, request):
        runner = get_current_runner()
        request.urlconf = runner.get_urls(request)
        return None        
