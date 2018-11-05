import unittest


def check_request_exists_keys(target, *keys):
    return all((key in target) for key in keys)


def check_request_str_values(target, *keys):
    return _check_request_values(lambda value: type(value) is str, target, *keys)


def _check_request_values(cond, target, *keys):
    return all(cond(target[key]) for key in keys)


class Test(unittest.TestCase):

    def test_check_request_exists_keys(self):
        self.assertTrue(check_request_exists_keys({'key': 'value'}, 'key'))
        self.assertFalse(check_request_exists_keys({'key': 'value'}, 'invalid'))

    def test_check_request_str_values(self):
        self.assertTrue(check_request_str_values({'key': 'value'}, 'key'))
        self.assertFalse(check_request_str_values({'key': None}, 'key'))
