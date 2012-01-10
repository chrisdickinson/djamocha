from djamocha import DjamochaTest

# usage: list of JS / CSS + list of JS tests
DjamochaTest(Form.media, tests)

# usage: list of JS / CSS + router
DjamochaTest(Form.media, tests, 'path.to.test.routes')


# bin/manage.py djamochatest
# bin/manage.py djamochaserve
