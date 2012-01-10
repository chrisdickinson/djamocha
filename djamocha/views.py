from djamocha.settings import configuration
from django.template.loader import get_template
from django.template import Template, Context, RequestContext

def serve_html(request, template_name=None, media=None, tests=None):
    template = (template_name and [get_template(template_name)] or [Template(DEFAULT_TEMPLATE)])[0] 
    media = media or {}
    tests = tests or {}

    return template.render(RequestContext(request, {
        'media':media,
        'tests':tests
    }))
