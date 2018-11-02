import unittest


def validate_coupon(coupon):
    return tuple(message for cond, message in (
        (_check_title_length, 'invalid.coupon_title_length'),
        (_check_description_length, 'invalid.coupon_description_length'),
    ) if not cond(coupon))


def _check_title_length(coupon):
    return 1 <= len(coupon['title']) <= 20


def _check_description_length(coupon):
    return len(coupon['description']) <= 100


class Test(unittest.TestCase):

    def test_validate_coupon(self):
        valid_coupon = {
            'title': 'title',
            'description': 'description',
        }
        print(validate_coupon(valid_coupon))
        self.assertEqual((), validate_coupon(valid_coupon))
        self.assertEqual((), validate_coupon({**valid_coupon, 'title': 'x'}))
        self.assertEqual((), validate_coupon({**valid_coupon, 'title': 'x' * 20}))
        self.assertEqual(('invalid.coupon_title_length',), validate_coupon({**valid_coupon, 'title': ''}))
        self.assertEqual(('invalid.coupon_title_length',), validate_coupon({**valid_coupon, 'title': 'x' * 21}))
        self.assertEqual((), validate_coupon({**valid_coupon, 'description': 'x' * 100}))
        self.assertEqual(('invalid.coupon_description_length',), validate_coupon({**valid_coupon, 'description': 'x' * 101}))
