RUNNER = None

class Context(object):
    def __init__(self):
        self.runner = None

    def get(self):
        return self.runner

    def set(self, runner):
        print "SETTING RUNNER TO ", runner
        self.runner = runner

ctxt = Context()

get_current_runner = ctxt.get
set_current_runner = ctxt.set
