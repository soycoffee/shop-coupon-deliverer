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
    return event['httpMethod'] == 'PUT' and 'id' in event['pathParameters']


def _match_delete_coupon(event):
    return event['httpMethod'] == 'DELETE' and 'id' in event['pathParameters']


def _match_query_coupons(event):
    return event['httpMethod'] == 'GET'


def _call_create_coupon(event):
    return create_coupon(
        event['body']['image'],
        event['body']['image_name'],
    )


def _call_read_coupon(event):
    return read_coupon()


def _call_update_coupon(event):
    return update_coupon()


def _call_delete_coupon(event):
    return delete_coupon()


def _call_query_coupons(event):
    return query_coupons()


class Test(unittest.TestCase):

    @mock.patch('lambda_handler.create_coupon')
    def test_create_coupon(self, mock_create_coupon):
        mock_create_coupon.return_value = 'create_coupon'
        response = lambda_handler({
            'httpMethod': 'POST',
            'body': {
                'image': 'image',
                'image_name': 'image_name',
            },
        }, {})
        self.assertEqual('create_coupon', response)
        mock_create_coupon.assert_called_once_with('image', 'image_name')

    @mock.patch('lambda_handler.read_coupon')
    def test_read_coupon(self, mock_read_coupon):
        mock_read_coupon.return_value = 'read_coupon'
        response = lambda_handler({
            'httpMethod': 'GET',
            'pathParameters': {
                'id': 1,
            },
        }, {})
        self.assertEqual('read_coupon', response)
        mock_read_coupon.assert_called_once_with()

    @mock.patch('lambda_handler.update_coupon')
    def test_update_coupon(self, mock_update_coupon):
        mock_update_coupon.return_value = 'update_coupon'
        response = lambda_handler({
            'httpMethod': 'PUT',
            'pathParameters': {
                'id': 1,
            },
            'body': {
                'image': 'image',
                'image_name': 'image_name',
            },
        }, {})
        self.assertEqual('update_coupon', response)
        mock_update_coupon.assert_called_once_with()

    @mock.patch('lambda_handler.delete_coupon')
    def test_delete_coupon(self, mock_delete_coupon):
        mock_delete_coupon.return_value = 'delete_coupon'
        response = lambda_handler({
            'httpMethod': 'DELETE',
            'pathParameters': {
                'id': 1,
            },
        }, {})
        self.assertEqual('delete_coupon', response)
        mock_delete_coupon.assert_called_once_with()

    @mock.patch('lambda_handler.query_coupons')
    def test_query_coupons(self, mock_query_coupons):
        mock_query_coupons.return_value = 'query_coupons'
        response = lambda_handler({
            'httpMethod': 'GET',
            'pathParameters': {},
            'body': {
                'image': 'image',
                'image_name': 'image_name',
            },
        }, {})
        self.assertEqual('query_coupons', response)
        mock_query_coupons.assert_called_once_with()

