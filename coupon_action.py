import unittest
from unittest import mock
from unittest.mock import MagicMock

from dynamodb_atomic_counts import dynamodb_atomic_count
from dynamodb_coupons import dynamodb_put_coupon, dynamodb_get_coupon
from s3_coupons import s3_put_coupon_image, s3_generate_coupon_url
from coupon_validation import validate_coupon
from error_response import build_bad_request_response


def create_coupon(title, description, image, image_name, qr_code_image, qr_code_image_name):
    coupon = {
        'title': title,
        'description': description,
    }
    validation_result = validate_coupon(coupon)
    if validation_result:
        return build_bad_request_response(*validation_result)
    image_object = s3_put_coupon_image(image, image_name)
    qr_code_image_object = s3_put_coupon_image(qr_code_image, qr_code_image_name)
    _id = str(dynamodb_atomic_count('coupon_id')).zfill(7)
    return dynamodb_put_coupon({
        **coupon,
        'id': _id,
        'image_s3_key': image_object.key,
        'qr_code_image_s3_key': qr_code_image_object.key,
    })


def read_coupon(_id):
    coupon = dynamodb_get_coupon(_id)
    image_url = s3_generate_coupon_url(coupon['image_s3_key'])
    return {
        **coupon,
        'image_url': image_url,
    }


def update_coupon(_id, title, description, image, image_name, qr_code_image, qr_code_image_name):
    image_object = s3_put_coupon_image(image, image_name)
    qr_code_image_object = s3_put_coupon_image(qr_code_image, qr_code_image_name)
    _id = str(dynamodb_atomic_count('coupon_id')).zfill(7)
    return dynamodb_put_coupon({
        'id': _id,
        'title': title,
        'description': description,
        'image_s3_key': image_object.key,
        'qr_code_image_s3_key': qr_code_image_object.key,
    })


def delete_coupon():
    pass


def query_coupons():
    pass


class Test(unittest.TestCase):

    @mock.patch('coupon_action.s3_put_coupon_image')
    @mock.patch('coupon_action.dynamodb_atomic_count')
    @mock.patch('coupon_action.dynamodb_put_coupon')
    def test_create_coupon(self, mock_dynamodb_put_coupon, mock_dynamodb_atomic_count, mock_s3_put_coupon_image):
        mock_s3_put_coupon_image.side_effect = [
            MagicMock(**{'key': 'image_s3_key'}),
            MagicMock(**{'key': 'qr_code_image_s3_key'}),
        ]
        mock_dynamodb_atomic_count.return_value = 1
        mock_dynamodb_put_coupon.return_value = 'coupon'
        response = create_coupon(
            'title',
            'description',
            'image',
            'image_name',
            'qr_code_image',
            'qr_code_image_name',
        )
        self.assertEqual('coupon', response)

        mock_s3_put_coupon_image.assert_has_calls([
            mock.call('image', 'image_name'),
            mock.call('qr_code_image', 'qr_code_image_name'),
        ])
        mock_dynamodb_atomic_count.assert_called_once_with('coupon_id')
        mock_dynamodb_put_coupon.assert_called_once_with({
            'id': '0000001',
            'title': 'title',
            'description': 'description',
            'image_s3_key': 'image_s3_key',
            'qr_code_image_s3_key': 'qr_code_image_s3_key',
        })

    def test_create_coupon_bad_request(self):
        self.assertEqual(
            {'statusCode': 400, 'body': {'messages': ('invalid.coupon_title_length',)}},
            create_coupon('', '', '', '', '', ''),
        )

    @mock.patch('coupon_action.dynamodb_get_coupon')
    @mock.patch('coupon_action.s3_generate_coupon_url')
    def test_read_coupon(self, mock_s3_generate_coupon_url, mock_dynamodb_get_coupon):
        mock_dynamodb_get_coupon.return_value = {
            'image_s3_key': 'image_s3_key',
        }
        mock_s3_generate_coupon_url.return_value = 'image_url'
        response = read_coupon('id')
        self.assertEqual({
            'image_s3_key': 'image_s3_key',
            'image_url': 'image_url',
        }, response)
        mock_dynamodb_get_coupon.assert_called_once_with('id')
        mock_s3_generate_coupon_url.assert_called_once_with('image_s3_key')
