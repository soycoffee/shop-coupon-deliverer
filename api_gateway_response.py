import json
import unittest


def build_ok_response(body, headers=None):
    return _build_response(200, body, headers)


def build_bad_request_response(*messages):
    return _build_error_response(400, messages)


def build_not_found_response(*messages):
    return _build_error_response(404, messages)


def _build_response(status_code, body, headers):
    return {
        'statusCode': status_code,
        'headers': (headers if headers is not None else {}),
        'body': json.dumps(body, ensure_ascii=False),
        'isBase64Encoded': False,
    }


def _build_error_response(status_code, messages):
    return _build_response(status_code, {'messages': messages}, {})


class Test(unittest.TestCase):

    def test_build_ok_response(self):
        self.assertEqual({
            'statusCode': 200,
            'headers': {},
            'body': '{"key": "value"}',
            'isBase64Encoded': False,
        }, build_ok_response({'key': 'value'}))
        self.assertEqual({
            'statusCode': 200,
            'headers': {},
            'body': 'null',
            'isBase64Encoded': False,
        }, build_ok_response(None))

    def test_build_bad_request_response(self):
        self.assertEqual({
            'statusCode': 400,
            'headers': {},
            'body': '{"messages": ["message"]}',
            'isBase64Encoded': False,
        }, build_bad_request_response('message'))
