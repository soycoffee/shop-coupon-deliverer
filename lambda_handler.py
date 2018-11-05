import json
import re
import unittest

from unittest import mock
from coupon_action import create_coupon, read_coupon, update_coupon, delete_coupon, query_coupons
from request_check import check_request_exists_keys, check_request_str_values
from api_gateway_response import build_bad_request_response, build_not_found_response


_ID_PATTERN = re.compile('\d+')


def lambda_handler(event, context):
    return next(call(event) for match, call in _route() if match(event))


def _route():
    return (
        (_match_create_coupon, _call_create_coupon),
        (_match_read_coupon, _call_read_coupon),
        (_match_update_coupon, _call_update_coupon),
        (_match_delete_coupon, _call_delete_coupon),
        (_match_query_coupons, _call_query_coupons),
        (lambda _: True, lambda _: build_not_found_response('route_not_found')),
    )


def _match_create_coupon(event):
    return event['httpMethod'] == 'POST' and _allowed_destructive_action(event)


def _match_read_coupon(event):
    return event['httpMethod'] == 'GET' and _has_valid_path_id(event)


def _match_update_coupon(event):
    return event['httpMethod'] == 'PUT' and _has_valid_path_id(event) and _allowed_destructive_action(event)


def _match_delete_coupon(event):
    return event['httpMethod'] == 'DELETE' and _has_valid_path_id(event) and _allowed_destructive_action(event)


def _match_query_coupons(event):
    return event['httpMethod'] == 'GET'


def _call_create_coupon(event):
    body = json.loads(event['body'])
    if not check_request_exists_keys(body, 'title', 'description', 'image', 'image_name', 'qr_code_image',
                                     'qr_code_image_name'):
        return build_bad_request_response('not_exists_key')
    if not check_request_str_values(body, 'title', 'description', 'image', 'image_name', 'qr_code_image',
                                    'qr_code_image_name'):
        return build_bad_request_response('invalid_type')
    return create_coupon(body['title'], body['description'], body['image'], body['image_name'], body['qr_code_image'],
                         body['qr_code_image_name'])


def _call_read_coupon(event):
    return read_coupon(_pick_path_id(event))


def _call_update_coupon(event):
    body = json.loads(event['body'])
    if not check_request_exists_keys(body, 'title', 'description', 'image', 'image_name', 'qr_code_image',
                                     'qr_code_image_name'):
        return build_bad_request_response('not_exists_key')
    if not check_request_str_values(body, 'title', 'description', 'image', 'image_name', 'qr_code_image',
                                    'qr_code_image_name'):
        return build_bad_request_response('invalid_type')
    return update_coupon(_pick_path_id(event), body['title'], body['description'], body['image'], body['image_name'],
                         body['qr_code_image'], body['qr_code_image_name'])


def _call_delete_coupon(event):
    return delete_coupon(_pick_path_id(event))


def _call_query_coupons(_):
    return query_coupons()


def _has_valid_path_id(event):
    return (
            'pathParameters' in event
            and type(event['pathParameters']) is dict
            and 'id' in event['pathParameters']
            and type(event['pathParameters']['id']) is str
            and _ID_PATTERN.fullmatch(event['pathParameters']['id'])
    )


def _pick_path_id(event):
    return event['pathParameters']['id']


def _allowed_destructive_action(event):
    api_key_id = event['requestContext']['identity']['apiKeyId']
    return (
            ('stageVariables' in event and 'administratorApiKeyId' in event['stageVariables']
             and api_key_id == event['stageVariables']['administratorApiKeyId'])
            or api_key_id == 'test-invoke-api-key-id'
    )


class Test(unittest.TestCase):

    @staticmethod
    def _with_test_api_key_id():
        return {'requestContext': {'identity': {'apiKeyId': 'test-invoke-api-key-id'}}}

    @mock.patch('lambda_handler.create_coupon')
    def test_create_coupon(self, mock_create_coupon):
        mock_create_coupon.return_value = 'coupon'
        response = lambda_handler({
            'httpMethod': 'POST',
            'body': json.dumps({
                'title': 'title',
                'description': 'description',
                'image': 'image',
                'image_name': 'image_name',
                'qr_code_image': 'qr_code_image',
                'qr_code_image_name': 'qr_code_image_name',
            }),
            **self._with_test_api_key_id(),
        }, {})
        self.assertEqual('coupon', response)
        mock_create_coupon.assert_called_once_with('title', 'description', 'image', 'image_name', 'qr_code_image',
                                                   'qr_code_image_name')

    def test_create_coupon_bad_request(self):
        self.assertEqual(
            build_bad_request_response('not_exists_key'),
            lambda_handler({'httpMethod': 'POST', 'body': '{}', **self._with_test_api_key_id()}, {}),
        )
        self.assertEqual(
            build_bad_request_response('invalid_type'),
            lambda_handler({
                'httpMethod': 'POST',
                'body': json.dumps({
                    'title': None,
                    'description': '',
                    'image': '',
                    'image_name': '',
                    'qr_code_image': '',
                    'qr_code_image_name': '',
                }),
                **self._with_test_api_key_id(),
            }, {}),
        )

    @mock.patch('lambda_handler.read_coupon')
    def test_read_coupon(self, mock_read_coupon):
        mock_read_coupon.return_value = 'coupon'
        response = lambda_handler({
            'httpMethod': 'GET',
            'pathParameters': {'id': '0000001'},
            **self._with_test_api_key_id(),
        }, {})
        self.assertEqual('coupon', response)
        mock_read_coupon.assert_called_once_with('0000001')

    @mock.patch('lambda_handler.update_coupon')
    def test_update_coupon(self, mock_update_coupon):
        mock_update_coupon.return_value = 'coupon'
        response = lambda_handler({
            'httpMethod': 'PUT',
            'pathParameters': {'id': '0000001'},
            'body': json.dumps({
                'title': 'title',
                'description': 'description',
                'image': 'image',
                'image_name': 'image_name',
                'qr_code_image': 'qr_code_image',
                'qr_code_image_name': 'qr_code_image_name',
            }),
            **self._with_test_api_key_id(),
        }, {})
        self.assertEqual('coupon', response)
        mock_update_coupon.assert_called_once_with('0000001', 'title', 'description', 'image', 'image_name',
                                                   'qr_code_image', 'qr_code_image_name')

    def test_update_coupon_bad_request(self):
        self.assertEqual(
            build_bad_request_response('not_exists_key'),
            lambda_handler({'httpMethod': 'PUT', 'pathParameters': {'id': '0000001'}, 'body': '{}',
                            **self._with_test_api_key_id()}, {}),
        )
        self.assertEqual(
            build_bad_request_response('invalid_type'),
            lambda_handler({
                'httpMethod': 'PUT',
                'pathParameters': {'id': '0000001'},
                'body': json.dumps({
                    'title': None,
                    'description': '',
                    'image': '',
                    'image_name': '',
                    'qr_code_image': '',
                    'qr_code_image_name': '',
                }),
                **self._with_test_api_key_id(),
            }, {}),
        )

    @mock.patch('lambda_handler.delete_coupon')
    def test_delete_coupon(self, mock_delete_coupon):
        mock_delete_coupon.return_value = 'coupon'
        response = lambda_handler({
            'httpMethod': 'DELETE',
            'pathParameters': {'id': '0000001'},
            **self._with_test_api_key_id(),
        }, {})
        self.assertEqual('coupon', response)
        mock_delete_coupon.assert_called_once_with('0000001')

    @mock.patch('lambda_handler.query_coupons')
    def test_query_coupons(self, mock_query_coupons):
        mock_query_coupons.return_value = 'coupons'
        response = lambda_handler({
            'httpMethod': 'GET',
            'pathParameters': None,
            'body': json.dumps({
                'image': 'image',
                'image_name': 'image_name',
            }),
            **self._with_test_api_key_id(),
        }, {})
        self.assertEqual('coupons', response)
        mock_query_coupons.assert_called_once_with()

    def test_route_not_found(self):
        self.assertEqual(
            build_not_found_response('route_not_found'),
            lambda_handler({'httpMethod': 'X', 'body': '{}', **self._with_test_api_key_id()}, {}),
        )

    def test_has_valid_path_id(self):
        self.assertTrue(_has_valid_path_id({'pathParameters': {'id': '0000001'}}))
        self.assertFalse(_has_valid_path_id({}))
        self.assertFalse(_has_valid_path_id({'pathParameters': None}))
        self.assertFalse(_has_valid_path_id({'pathParameters': {}}))
        self.assertFalse(_has_valid_path_id({'pathParameters': {'id': 1}}))
        self.assertFalse(_has_valid_path_id({'pathParameters': {'id': ''}}))

    @mock.patch('lambda_handler._call_create_coupon')
    @mock.patch('lambda_handler._call_update_coupon')
    @mock.patch('lambda_handler._call_delete_coupon')
    def test_allowed_destructive_action(self, mock_call_delete_coupon, mock_call_update_coupon,
                                        mock_call_create_coupon):
        with_stage_api_key_id = {
            'requestContext': {'identity': {'apiKeyId': 'administrator'}},
            'stageVariables': {'administratorApiKeyId': 'administrator'},
        }
        lambda_handler({'httpMethod': 'POST', 'body': '{}', **with_stage_api_key_id}, {})
        mock_call_create_coupon.assert_called_once()
        lambda_handler({'httpMethod': 'PUT', 'body': '{}', 'pathParameters': {'id': '0000001'},
                        **with_stage_api_key_id}, {}),
        mock_call_update_coupon.assert_called_once()
        lambda_handler({'httpMethod': 'DELETE', 'body': '{}', 'pathParameters': {'id': '0000001'},
                        **with_stage_api_key_id}, {}),
        mock_call_delete_coupon.assert_called_once()

    def test_allowed_destructive_action_not_found(self):
        with_denied_api_key = {'requestContext': {'identity': {'apiKeyId': 'denied'}}}
        self.assertEqual(
            build_not_found_response('route_not_found',),
            lambda_handler({'httpMethod': 'POST', 'body': '{}', **with_denied_api_key}, {}),
        )
        self.assertEqual(
            build_not_found_response('route_not_found',),
            lambda_handler({'httpMethod': 'PUT', 'body': '{}', 'pathParameters': {'id': '0000001'},
                            **with_denied_api_key}, {}),
        )
        self.assertEqual(
            build_not_found_response('route_not_found',),
            lambda_handler({'httpMethod': 'DELETE', 'body': '{}', 'pathParameters': {'id': '0000001'},
                            **with_denied_api_key}, {}),
        )
