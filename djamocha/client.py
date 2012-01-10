class Client(object):
    def __init__(self, uuid, request):
        self.uuid = uuid
        self.tests = []
        # TODO: add browser sniffing.

    def next_test(self):
        next = self.tests.pop()
        if not len(self.tests):
            return '/done/'
        return '/'

    def set_tests(self, tests):
        self.tests = tests

