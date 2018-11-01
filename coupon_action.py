import unittest
from unittest import mock
from unittest.mock import MagicMock
from dynamodb_atomic_counts import dynamodb_atomic_count
from dynamodb_coupons import dynamodb_put_coupon
from s3_coupon_image import s3_put_coupon_image


def create_coupon(image, image_name):
    image_object = s3_put_coupon_image(image, image_name)
    _id = str(dynamodb_atomic_count('coupon_id')).zfill(7)
    return dynamodb_put_coupon({
        'id': _id,
        'image_s3_key': image_object.key,
    })


def read_coupon():
    pass


def update_coupon():
    pass


def delete_coupon():
    pass


def query_coupons():
    pass


class Test(unittest.TestCase):

    @mock.patch('coupon_action.s3_put_coupon_image')
    @mock.patch('coupon_action.dynamodb_atomic_count')
    @mock.patch('coupon_action.dynamodb_put_coupon')
    def test_create_coupon(self, mock_dynamodb_put_coupon, mock_dynamodb_atomic_count, mock_s3_put_coupon_image):
        mock_image_object = MagicMock()
        mock_image_object.key = 'image_s3_key'
        mock_s3_put_coupon_image.return_value = mock_image_object
        mock_dynamodb_atomic_count.return_value = 1
        mock_dynamodb_put_coupon.return_value = 'coupon'
        response = create_coupon('image', 'image_name')
        self.assertEqual('coupon', response)
        mock_s3_put_coupon_image.assert_called_once_with('image', 'image_name')
        mock_dynamodb_atomic_count.assert_called_once_with('coupon_id')
        mock_dynamodb_put_coupon.assert_called_once_with({
            'id': '0000001',
            'image_s3_key': 'image_s3_key',
        })
