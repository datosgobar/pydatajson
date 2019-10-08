from unittest import TestCase

from pydatajson.threading_helper import apply_threading


class ThreadingTests(TestCase):

    def test_threading(self):
        elements = [1, 2, 3, 4]

        def function(x):
            return x ** 2

        result = apply_threading(elements, function, 3)

        self.assertEqual(result, [1, 4, 9, 16])
