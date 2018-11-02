import unittest


def validate_exists_keys(target, *keys):
    return all((key in target) for key in keys)


def validate_str_values(target, *keys):
    return _validate_values(lambda value: type(value) is str, target, *keys)


def _validate_values(cond, target, *keys):
    return all(cond(target[key]) for key in keys)


class Test(unittest.TestCase):

    def test_validate_exists_keys(self):
        self.assertTrue(validate_exists_keys({'key': 'value'}, 'key'))
        self.assertFalse(validate_exists_keys({'key': 'value'}, 'invalid'))

    def test_validate_str_values(self):
        self.assertTrue(validate_str_values({'key': 'value'}, 'key'))
        self.assertFalse(validate_str_values({'key': None}, 'key'))
