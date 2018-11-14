import json
import uuid
import unittest
from unittest import mock
from unittest.mock import MagicMock

from dynamodb_atomic_counts import dynamodb_increment_atomic_count
from dynamodb_coupons import dynamodb_put_coupon, dynamodb_get_coupon, dynamodb_query_coupons, dynamodb_delete_coupon
from s3_coupons import s3_put_coupon_image, s3_delete_coupon_image, s3_generate_coupon_url
from coupon_validation import validate_coupon
from api_gateway_response import build_ok_response, build_bad_request_response, build_not_found_response


_PAGINATION_COUNT = 20


def create_coupon(title, description, image, qr_code_image):
    return _write_coupon(title, description, image, qr_code_image,
                         lambda: str(dynamodb_increment_atomic_count('coupon_id')).zfill(7))


def read_coupon(_id):
    get_coupon_result = dynamodb_get_coupon(_id)
    if 'Item' not in get_coupon_result:
        return build_not_found_response('coupon_not_found')
    coupon = get_coupon_result['Item']
    return build_ok_response({**_delete_fixed_key(coupon), **_with_s3_urls(coupon)})


def update_coupon(_id, title, description, image, qr_code_image):
    get_coupon_result = dynamodb_get_coupon(_id)
    if 'Item' not in get_coupon_result:
        return build_not_found_response('coupon_not_found')
    old_coupon = get_coupon_result['Item']
    response = _write_coupon(title, description, image, qr_code_image, lambda: _id)
    if response['statusCode'] == 200:
        s3_delete_coupon_image(old_coupon['image_s3_key'])
        s3_delete_coupon_image(old_coupon['qr_code_image_s3_key'])
    return response


def delete_coupon(_id):
    get_coupon_result = dynamodb_get_coupon(_id)
    if 'Item' not in get_coupon_result:
        return build_not_found_response('coupon_not_found')
    coupon = get_coupon_result['Item']
    dynamodb_delete_coupon(coupon['id'])
    s3_delete_coupon_image(coupon['image_s3_key'])
    s3_delete_coupon_image(coupon['qr_code_image_s3_key'])
    return build_ok_response(None)


def query_coupons(last_evaluated_key):
    query_coupons_result = dynamodb_query_coupons(last_evaluated_key)
    return build_ok_response(
        tuple({**_delete_fixed_key(coupon), **_with_s3_urls(coupon)}
              for coupon in query_coupons_result['Items']),
        {
            **({'Last-Evaluated-Key': json.dumps(query_coupons_result['LastEvaluatedKey'])}
               if 'LastEvaluatedKey' in query_coupons_result else {})
        },
    )


def _write_coupon(title, description, image, qr_code_image, id_provider):
    coupon = {
        'title': title,
        'description': description,
    }
    validation_result = validate_coupon(coupon)
    if validation_result:
        return build_bad_request_response(*validation_result)
    (image_mime_type, image_body) = _extract_data_url(image)
    if image_mime_type is None or image_body is None:
        return build_bad_request_response('invalid.image')
    (qr_code_image_mime_type, qr_code_image_body) = _extract_data_url(qr_code_image)
    if qr_code_image_mime_type is None or qr_code_image_body is None:
        return build_bad_request_response('invalid.qr_code_image')
    image_object = s3_put_coupon_image(_make_s3_key('image'), image_body, image_mime_type)
    qr_code_image_object = s3_put_coupon_image(_make_s3_key('qr_code_image'), qr_code_image_body,
                                               qr_code_image_mime_type)
    _id = id_provider()
    dynamodb_put_coupon({
        **coupon,
        'id': _id,
        'image_s3_key': image_object.key,
        'qr_code_image_s3_key': qr_code_image_object.key,
    })
    result_coupon = dynamodb_get_coupon(_id)['Item']
    return build_ok_response(result_coupon)


def _extract_data_url(source):
    colon_index = source.find(':')
    semicolon_index = source.find(';')
    comma_index = source.find(',')
    mime_type = source[(colon_index + 1):semicolon_index] if colon_index != -1 and semicolon_index != -1 else None
    encoded_image = source[(comma_index + 1):] if comma_index != -1 else None
    return mime_type, encoded_image


def _make_s3_key(directory):
    return f"{directory}/{str(uuid.uuid4())}"


def _with_s3_urls(coupon):
    return {
        'image_url': s3_generate_coupon_url(coupon['image_s3_key']),
        'qr_code_image_url': s3_generate_coupon_url(coupon['qr_code_image_s3_key']),
    }


def _delete_fixed_key(coupon):
    del coupon['fixed_key']
    return coupon


class Test(unittest.TestCase):

    @mock.patch('coupon_action.dynamodb_put_coupon')
    @mock.patch('coupon_action.dynamodb_get_coupon')
    @mock.patch('coupon_action.dynamodb_increment_atomic_count')
    @mock.patch('coupon_action.s3_put_coupon_image')
    @mock.patch('coupon_action.uuid.uuid4')
    def test_create_coupon(self, mock_uuid4, mock_s3_put_coupon_image, mock_dynamodb_increment_atomic_count,
                           mock_dynamodb_get_coupon, mock_dynamodb_put_coupon):
        mock_uuid4.return_value = 'fixed_uuid'
        mock_s3_put_coupon_image.side_effect = [MagicMock(key='image_s3_key'), MagicMock(key='qr_code_image_s3_key')]
        mock_dynamodb_increment_atomic_count.return_value = 1
        mock_dynamodb_get_coupon.return_value = {'Item': {'id': '0000001'}}
        response = create_coupon('title', 'description', 'data:image/png;base64,image',
                                 'data:image/png;base64,qr_code_image')
        self.assertEqual(build_ok_response({'id': '0000001'}), response)
        mock_s3_put_coupon_image.assert_has_calls([
            mock.call('image/fixed_uuid', 'image', 'image/png'),
            mock.call('qr_code_image/fixed_uuid', 'qr_code_image', 'image/png'),
        ])
        mock_dynamodb_increment_atomic_count.assert_called_once_with('coupon_id')
        mock_dynamodb_put_coupon.assert_called_once_with({
            'id': '0000001',
            'title': 'title',
            'description': 'description',
            'image_s3_key': 'image_s3_key',
            'qr_code_image_s3_key': 'qr_code_image_s3_key',
        })
        mock_dynamodb_get_coupon.assert_called_once_with('0000001')

    def test_create_coupon_validation(self):
        self.assertEqual(
            build_bad_request_response('invalid.coupon_title_length'),
            create_coupon('', '', '', ''),
        )

    def test_create_coupon_invalid_image(self):
        self.assertEqual(
            build_bad_request_response('invalid.image'),
            create_coupon('title', '', 'invalid', 'data:image/png;base64,qr_code_image'),
        )
        self.assertEqual(
            build_bad_request_response('invalid.qr_code_image'),
            create_coupon('title', '', 'data:image/png;base64,qr_code_image', ''),
        )

    @mock.patch('coupon_action.dynamodb_get_coupon')
    @mock.patch('coupon_action.s3_generate_coupon_url')
    def test_read_coupon(self, mock_s3_generate_coupon_url, mock_dynamodb_get_coupon):
        mock_dynamodb_get_coupon.return_value = {
            'Item': {'image_s3_key': 'image_s3_key', 'qr_code_image_s3_key': 'qr_code_image_s3_key', 'fixed_key': ''}
        }
        mock_s3_generate_coupon_url.side_effect = ['image_url', 'qr_code_image_url']
        response = read_coupon('id')
        self.assertEqual(build_ok_response({
            'image_s3_key': 'image_s3_key',
            'qr_code_image_s3_key': 'qr_code_image_s3_key',
            'image_url': 'image_url',
            'qr_code_image_url': 'qr_code_image_url',
        }), response)
        mock_dynamodb_get_coupon.assert_called_once_with('id')
        mock_s3_generate_coupon_url.assert_has_calls([mock.call('image_s3_key'), mock.call('qr_code_image_s3_key')])

    @mock.patch('coupon_action.dynamodb_get_coupon')
    def test_read_coupon_not_found(self, mock_dynamodb_get_coupon):
        mock_dynamodb_get_coupon.return_value = {}
        response = read_coupon('0000001')
        self.assertEqual(build_not_found_response('coupon_not_found'), response)
        mock_dynamodb_get_coupon.assert_called_once_with('0000001')

    @mock.patch('coupon_action.dynamodb_put_coupon')
    @mock.patch('coupon_action.dynamodb_get_coupon')
    @mock.patch('coupon_action.s3_put_coupon_image')
    @mock.patch('coupon_action.s3_delete_coupon_image')
    @mock.patch('coupon_action.uuid.uuid4')
    def test_update_coupon(self, mock_uuid4, mock_s3_delete_coupon_image, mock_s3_put_coupon_image,
                           mock_dynamodb_get_coupon, mock_dynamodb_put_coupon):
        mock_uuid4.return_value = 'fixed_uuid'
        mock_s3_put_coupon_image.side_effect = [MagicMock(key='image_s3_key'), MagicMock(key='qr_code_image_s3_key')]
        mock_dynamodb_get_coupon.return_value = {'Item': {
            'id': '0000001',
            'image_s3_key': 'image_s3_key',
            'qr_code_image_s3_key': 'qr_code_image_s3_key',
        }}
        response = update_coupon('0000001', 'title', 'description', 'data:image/png;base64,image',
                                 'data:image/png;base64,qr_code_image')
        self.assertEqual(build_ok_response({
            'id': '0000001',
            'image_s3_key': 'image_s3_key',
            'qr_code_image_s3_key': 'qr_code_image_s3_key',
        }), response)
        mock_s3_put_coupon_image.assert_has_calls([
            mock.call('image/fixed_uuid', 'image', 'image/png'),
            mock.call('qr_code_image/fixed_uuid', 'qr_code_image', 'image/png'),
        ])
        mock_dynamodb_put_coupon.assert_called_once_with({
            'id': '0000001',
            'title': 'title',
            'description': 'description',
            'image_s3_key': 'image_s3_key',
            'qr_code_image_s3_key': 'qr_code_image_s3_key',
        })
        mock_dynamodb_get_coupon.assert_has_calls([mock.call('0000001'), mock.call('0000001')])
        mock_s3_delete_coupon_image.assert_has_calls([mock.call('image_s3_key'), mock.call('qr_code_image_s3_key')])

    @mock.patch('coupon_action.dynamodb_get_coupon')
    def test_update_coupon_validation(self, mock_dynamodb_get_coupon):
        mock_dynamodb_get_coupon.return_value = {'Item': 'coupon'}
        response = update_coupon('', '', '', '', '')
        self.assertEqual(build_bad_request_response('invalid.coupon_title_length'), response)
        mock_dynamodb_get_coupon.assert_called_once_with('')

    @mock.patch('coupon_action.dynamodb_get_coupon')
    def test_update_coupon_invalid_image(self, mock_dynamodb_get_coupon):
        mock_dynamodb_get_coupon.return_value = {'Item': 'coupon'}
        self.assertEqual(
            build_bad_request_response('invalid.image'),
            create_coupon('title', '', 'invalid', 'data:image/png;base64,qr_code_image'),
        )
        self.assertEqual(
            build_bad_request_response('invalid.qr_code_image'),
            create_coupon('title', '', 'data:image/png;base64,qr_code_image', ''),
        )

    @mock.patch('coupon_action.dynamodb_get_coupon')
    def test_update_coupon_not_found(self, mock_dynamodb_get_coupon):
        mock_dynamodb_get_coupon.return_value = {}
        response = update_coupon('0000001', '', '', '', '')
        self.assertEqual(build_not_found_response('coupon_not_found'), response)
        mock_dynamodb_get_coupon.assert_called_once_with('0000001')

    @mock.patch('coupon_action.dynamodb_delete_coupon')
    @mock.patch('coupon_action.dynamodb_get_coupon')
    @mock.patch('coupon_action.s3_delete_coupon_image')
    def test_delete_coupon(self, mock_s3_delete_coupon_image, mock_dynamodb_get_coupon, mock_dynamodb_delete_coupon):
        mock_dynamodb_get_coupon.return_value = {
            'Item': {'id': '0000001', 'image_s3_key': 'image_s3_key', 'qr_code_image_s3_key': 'qr_code_image_s3_key'}
        }
        response = delete_coupon('0000001')
        self.assertEqual(build_ok_response(None), response)
        mock_dynamodb_get_coupon.assert_called_once_with('0000001')
        mock_dynamodb_delete_coupon.assert_called_once_with('0000001')
        mock_s3_delete_coupon_image.assert_has_calls([mock.call('image_s3_key'), mock.call('qr_code_image_s3_key')])

    @mock.patch('coupon_action.dynamodb_get_coupon')
    def test_delete_coupon_not_found(self, mock_dynamodb_get_coupon):
        mock_dynamodb_get_coupon.return_value = {}
        response = delete_coupon('0000001')
        self.assertEqual(build_not_found_response('coupon_not_found'), response)
        mock_dynamodb_get_coupon.assert_called_once_with('0000001')

    @mock.patch('coupon_action.dynamodb_query_coupons')
    @mock.patch('coupon_action.s3_generate_coupon_url')
    def test_query_coupons(self, mock_s3_generate_coupon_url, mock_dynamodb_query_coupons):
        mock_dynamodb_query_coupons.return_value = {
            'Items': [
                {
                    'image_s3_key': 'image_s3_key_0',
                    'qr_code_image_s3_key': 'qr_code_image_s3_key_0',
                    'fixed_key': '',
                },
                {
                    'image_s3_key': 'image_s3_key_1',
                    'qr_code_image_s3_key': 'qr_code_image_s3_key_1',
                    'fixed_key': '',
                },
            ],
            'LastEvaluatedKey': {'key': 'value'},
        }
        mock_s3_generate_coupon_url.side_effect = ['image_url_0', 'qr_code_image_url_0', 'image_url_1',
                                                   'qr_code_image_url_1']
        response = query_coupons('lastKey')
        self.assertEqual(build_ok_response(
            (
                {
                    'image_s3_key': 'image_s3_key_0',
                    'qr_code_image_s3_key': 'qr_code_image_s3_key_0',
                    'image_url': 'image_url_0',
                    'qr_code_image_url': 'qr_code_image_url_0',
                },
                {
                    'image_s3_key': 'image_s3_key_1',
                    'qr_code_image_s3_key': 'qr_code_image_s3_key_1',
                    'image_url': 'image_url_1',
                    'qr_code_image_url': 'qr_code_image_url_1',
                },
            ),
            {'Last-Evaluated-Key': '{"key": "value"}'},
        ), response)
        mock_dynamodb_query_coupons.assert_called_once_with('lastKey')
        mock_s3_generate_coupon_url.assert_has_calls([mock.call('image_s3_key_0'), mock.call('qr_code_image_s3_key_0'),
                                                      mock.call('image_s3_key_1'), mock.call('qr_code_image_s3_key_1')])

    @mock.patch('coupon_action.dynamodb_query_coupons')
    def test_query_coupons_no_last_evaluated_key(self, mock_dynamodb_query_coupons):
        mock_dynamodb_query_coupons.return_value = {'Items': []}
        response = query_coupons(None)
        self.assertEqual(build_ok_response(()), response)
        mock_dynamodb_query_coupons.assert_called_once_with(None)

    def test_extract_data_url(self):
        self.assertEqual(('image/png', 'foo'), _extract_data_url('data:image/png;base64,foo'))
        self.assertEqual((None, 'foo'), _extract_data_url('image/png;base64,foo'))
        self.assertEqual((None, 'foo'), _extract_data_url('data:base64,foo'))
        self.assertEqual(('image/png', None), _extract_data_url('data:image/png;foo'))
        self.assertEqual((None, None), _extract_data_url('foo'))
