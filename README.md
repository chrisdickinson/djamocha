# Djamocha

Integrating [Django](http://djangoproject.com/) and [Mocha](https://mochajs.org/) for
great good.

## But how?

Djamocha, lovingly named after a sort-of-gross-but-sometimes-appealing [beverage from Arby's](http://arbys.com/menu/shakes-desserts/jamocha-shake.html),
provides a new management command: `djamochatest` and a metaclass DSL for defining tests.

### How does it work?

* Djamocha is designed to run a single browser against the entire test suite at a time, automatically.

Djamocha looks for subclasses of `djamocha.Test` using the same process that `manage.py test` looks
for unit tests. Running `manage.py djamochatest` will run `manage.py testserver` in the background,
and tell you to hit `http://localhost:8000/idle/`. When you do so, it will automatically open up a
popup that cycles through all of your Djamocha test cases. When it finishes, your command line
program will exit with the number of failures as its exit code. If you wish to run again, assuming
your browser is still on the `idle` page, you can simply rerun the management command.

While a test suite is running, it assumes full control over the URL structure of your Django app --
you may provide a link to a `urls.py`, a `patterns` object, or nothing at all in your test -- and
stub XHR-based views this way.

Djamocha automatically runs a static server that provides your `Media`, excluding your tests.

Your tests are pulled from a `js` directory alongside the test file containing the unit test,
which allows you to keep your JavaScript tests separate from your static media.

## The DSL

The python side of things:

````python
# myapp/tests/jstests.py

import djamocha

class JSTest(djamocha.Test):
    # the media to be tested
    class Media:
        css = {}
        js = []

    # the routes that will be available while this 
    # test case is running
    routes = 'routes.for.my.app' 

    # the tests to run against that media
    tests = ['some.test.js']

````

You may define as many of these as you like in a single file.

`routes` accepts a string (to import) or a `patterns` object. You may use this
to stub out XHR requests (or perform full stack testing -- up to you!) 

`tests` is a list of JavaScript files containing Mocha test suites to pull from the
current test's adjacent `js` directory. You have access to jQuery, `suite`, `test`,
and `assert` (patterned off of [Node's assert module](http://nodejs.org/api/assert.html)).

A look at our JavaScript:

````javascript
// myapp/tests/js/some.test.js

suite("test", function() {
  test("hello world", function() {
    assert.equal(2, 1 + 1)
  })
})

````

## LICENSE

new BSD
