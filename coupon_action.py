import uuid
import unittest
from unittest import mock
from unittest.mock import MagicMock

from dynamodb_atomic_counts import dynamodb_atomic_count
from dynamodb_coupons import dynamodb_put_coupon, dynamodb_get_coupon, dynamodb_query_coupons, dynamodb_delete_coupon
from s3_coupons import s3_put_coupon_image, s3_delete_coupon_image, s3_generate_coupon_url
from coupon_validation import validate_coupon
from api_gateway_response import build_ok_response, build_bad_request_response, build_not_found_response


def create_coupon(title, description, image, image_name, qr_code_image, qr_code_image_name):
    return _write_coupon(title, description, image, image_name, qr_code_image, qr_code_image_name,
                         lambda: str(dynamodb_atomic_count('coupon_id')).zfill(7))


def read_coupon(_id):
    coupon_get_result = dynamodb_get_coupon(_id)
    if 'Item' not in coupon_get_result:
        return build_not_found_response('coupon_not_found')
    coupon = coupon_get_result['Item']
    return build_ok_response({**coupon, **_with_s3_urls(coupon)})


def update_coupon(_id, title, description, image, image_name, qr_code_image, qr_code_image_name):
    if 'Item' not in dynamodb_get_coupon(_id):
        return build_not_found_response('coupon_not_found')
    return _write_coupon(title, description, image, image_name, qr_code_image, qr_code_image_name, lambda: _id)


def delete_coupon(_id):
    coupon_get_result = dynamodb_get_coupon(_id)
    if 'Item' not in coupon_get_result:
        return build_not_found_response('coupon_not_found')
    coupon = coupon_get_result['Item']
    dynamodb_delete_coupon(coupon['id'])
    s3_delete_coupon_image(coupon['image_s3_key'])
    s3_delete_coupon_image(coupon['qr_code_image_s3_key'])
    return build_ok_response(None)


def query_coupons(page):
    return build_ok_response(
        tuple({**coupon, **_with_s3_urls(coupon)}
              for coupon in dynamodb_query_coupons(page)['Items']),
    )


def _write_coupon(title, description, image, image_name, qr_code_image, qr_code_image_name, id_provider):
    coupon = {
        'title': title,
        'description': description,
    }
    validation_result = validate_coupon(coupon)
    if validation_result:
        return build_bad_request_response(*validation_result)
    image_object = s3_put_coupon_image(_make_s3_key('image', image_name), image)
    qr_code_image_object = s3_put_coupon_image(_make_s3_key('qr_code_image', qr_code_image_name), qr_code_image)
    _id = id_provider()
    page = int(_id[:-2])
    dynamodb_put_coupon({
        **coupon,
        'id': _id,
        'image_s3_key': image_object.key,
        'qr_code_image_s3_key': qr_code_image_object.key,
        'page': page,
    })
    return build_ok_response(dynamodb_get_coupon(_id)['Item'])


def _make_s3_key(directory, _id):
    return f"{directory}/{str(uuid.uuid5(uuid.NAMESPACE_OID, _id))}"


def _with_s3_urls(coupon):
    return {
        'image_url': s3_generate_coupon_url(coupon['image_s3_key']),
        'qr_code_image_url': s3_generate_coupon_url(coupon['qr_code_image_s3_key']),
    }


class Test(unittest.TestCase):

    @mock.patch('coupon_action.dynamodb_put_coupon')
    @mock.patch('coupon_action.dynamodb_get_coupon')
    @mock.patch('coupon_action.dynamodb_atomic_count')
    @mock.patch('coupon_action.s3_put_coupon_image')
    def test_create_coupon(self, mock_s3_put_coupon_image, mock_dynamodb_atomic_count, mock_dynamodb_get_coupon,
                           mock_dynamodb_put_coupon):
        mock_s3_put_coupon_image.side_effect = [MagicMock(key='image_s3_key'), MagicMock(key='qr_code_image_s3_key')]
        mock_dynamodb_atomic_count.return_value = 1
        mock_dynamodb_get_coupon.return_value = {'Item': 'coupon'}
        response = create_coupon('title', 'description', 'image', 'image_name', 'qr_code_image', 'qr_code_image_name')
        self.assertEqual(build_ok_response('coupon'), response)
        mock_s3_put_coupon_image.assert_has_calls([
            mock.call('image/677ca515-751f-58d3-9778-8e6c20473171', 'image'),
            mock.call('qr_code_image/3853e016-d587-5cf6-b793-50cbf665cdb9', 'qr_code_image'),
        ])
        mock_dynamodb_atomic_count.assert_called_once_with('coupon_id')
        mock_dynamodb_put_coupon.assert_called_once_with({
            'id': '0000001',
            'title': 'title',
            'description': 'description',
            'image_s3_key': 'image_s3_key',
            'qr_code_image_s3_key': 'qr_code_image_s3_key',
            'page': 0,
        })
        mock_dynamodb_get_coupon.assert_called_once_with('0000001')

    def test_create_coupon_bad_request(self):
        self.assertEqual(
            build_bad_request_response('invalid.coupon_title_length'),
            create_coupon('', '', '', '', '', ''),
        )

    @mock.patch('coupon_action.dynamodb_get_coupon')
    @mock.patch('coupon_action.s3_generate_coupon_url')
    def test_read_coupon(self, mock_s3_generate_coupon_url, mock_dynamodb_get_coupon):
        mock_dynamodb_get_coupon.return_value = {
            'Item': {'image_s3_key': 'image_s3_key', 'qr_code_image_s3_key': 'qr_code_image_s3_key'}
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
    def test_update_coupon(self, mock_s3_put_coupon_image, mock_dynamodb_get_coupon, mock_dynamodb_put_coupon):
        mock_s3_put_coupon_image.side_effect = [MagicMock(key='image_s3_key'), MagicMock(key='qr_code_image_s3_key')]
        mock_dynamodb_get_coupon.return_value = {'Item': 'coupon'}
        response = update_coupon('0000001', 'title', 'description', 'image', 'image_name', 'qr_code_image',
                                 'qr_code_image_name')
        self.assertEqual(build_ok_response('coupon'), response)
        mock_s3_put_coupon_image.assert_has_calls([
            mock.call('image/677ca515-751f-58d3-9778-8e6c20473171', 'image'),
            mock.call('qr_code_image/3853e016-d587-5cf6-b793-50cbf665cdb9', 'qr_code_image'),
        ])
        mock_dynamodb_put_coupon.assert_called_once_with({
            'id': '0000001',
            'title': 'title',
            'description': 'description',
            'image_s3_key': 'image_s3_key',
            'qr_code_image_s3_key': 'qr_code_image_s3_key',
            'page': 0,
        })
        mock_dynamodb_get_coupon.assert_has_calls([mock.call('0000001'), mock.call('0000001')])

    @mock.patch('coupon_action.dynamodb_get_coupon')
    def test_update_coupon_not_found(self, mock_dynamodb_get_coupon):
        mock_dynamodb_get_coupon.return_value = {}
        response = update_coupon('0000001', '', '', '', '', '', '')
        self.assertEqual(build_not_found_response('coupon_not_found'), response)
        mock_dynamodb_get_coupon.assert_called_once_with('0000001')

    @mock.patch('coupon_action.dynamodb_get_coupon')
    def test_update_coupon_bad_request(self, mock_dynamodb_get_coupon):
        mock_dynamodb_get_coupon.return_value = {'Item': 'coupon'}
        response = update_coupon('', '', '', '', '', '', '')
        self.assertEqual(build_bad_request_response('invalid.coupon_title_length'), response)
        mock_dynamodb_get_coupon.assert_called_once_with('')

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
                {'image_s3_key': 'image_s3_key_0', 'qr_code_image_s3_key': 'qr_code_image_s3_key_0'},
                {'image_s3_key': 'image_s3_key_1', 'qr_code_image_s3_key': 'qr_code_image_s3_key_1'},
            ],
        }
        mock_s3_generate_coupon_url.side_effect = ['image_url_0', 'qr_code_image_url_0', 'image_url_1',
                                                   'qr_code_image_url_1']
        response = query_coupons(0)
        self.assertEqual(build_ok_response((
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
        )), response)
        mock_dynamodb_query_coupons.assert_called_once_with(0)
        mock_s3_generate_coupon_url.assert_has_calls([mock.call('image_s3_key_0'), mock.call('qr_code_image_s3_key_0'),
                                                      mock.call('image_s3_key_1'), mock.call('qr_code_image_s3_key_1')])
