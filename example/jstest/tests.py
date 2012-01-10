"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
import djamocha

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class JSTest(djamocha.Test):
    class Media:
        css = {}
        js = [
            'asdf.js'
        ]

    tests = ['some.test.js']
