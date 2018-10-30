import unittest
from unittest import mock
from create_coupon import create_coupon
from read_coupon import read_coupon
from update_coupon import update_coupon
from delete_coupon import delete_coupon
from query_coupons import query_coupons


def lambda_handler(event, context):
    return next(call(event) for match, call in _route() if match(event))


def _route():
    return (
        (_match_create_coupon, _call_create_coupon),
        (_match_read_coupon, _call_read_coupon),
        (_match_update_coupon, _call_update_coupon),
        (_match_delete_coupon, _call_delete_coupon),
        (_match_query_coupons, _call_query_coupons),
    )

def _match_create_coupon(event):
    return event['httpMethod'] == 'POST'


def _match_read_coupon(event):
    return event['httpMethod'] == 'GET' and 'id' in event['pathParameters']


def _match_update_coupon(event):
    return event['httpMethod'] == 'PUT'


def _match_delete_coupon(event):
    return event['httpMethod'] == 'DELETE'


def _match_query_coupons(event):
    return event['httpMethod'] == 'GET'


def _call_create_coupon(event):
    return create_coupon(
        event['body']['image'],
        event['body']['image_name'],
    )


def _call_read_coupon(event):
    read_coupon()


def _call_update_coupon(event):
    update_coupon()


def _call_delete_coupon(event):
    delete_coupon()


def _call_query_coupons(event):
    query_coupons()


class Test(unittest.TestCase):

    @mock.patch('__main__.create_coupon.create_coupon')
    def test_create_coupon(self, mock_create_coupon):
        mock_create_coupon.return_value = 'create_coupon'
        response = lambda_handler({
            'httpMethod': 'POST',
            'body': {
                'image': 'image',
                'image_name': 'image_name',
            },
        }, {})
        self.assertEqual(response, 'create_coupon')

