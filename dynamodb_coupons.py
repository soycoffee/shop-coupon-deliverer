import functools
import unittest
from unittest import mock
from unittest.mock import MagicMock

import boto3
from boto3.dynamodb.conditions import Key


_FIXED_KEY_VALUE = 'fixed_key'
_QUERY_LIMIT = 20


def dynamodb_put_coupon(item):
    return _dynamodb_coupons_table().put_item(Item={**item, **{'fixed_key': _FIXED_KEY_VALUE}})


def dynamodb_get_coupon(_id):
    return _dynamodb_coupons_table().get_item(Key={'id': _id})


def dynamodb_query_coupons(exclusive_start_key):
    return _dynamodb_coupons_table().query(
        IndexName='fixed_key-id-index',
        KeyConditionExpression=Key('fixed_key').eq(_FIXED_KEY_VALUE),
        Limit=_QUERY_LIMIT,
        **({'ExclusiveStartKey': exclusive_start_key} if exclusive_start_key is not None else {}),
    )


def dynamodb_delete_coupon(_id):
    return _dynamodb_coupons_table().delete_item(Key={'id': _id})


@functools.lru_cache()
def _dynamodb_coupons_table():
    return boto3.resource('dynamodb').Table('coupons')


class Test(unittest.TestCase):

    @mock.patch('dynamodb_coupons._dynamodb_coupons_table')
    def test_dynamodb_put_coupon(self, mock_dynamodb_coupons_table):
        mock.patch()
        mock_put_item = MagicMock()
        mock_dynamodb_coupons_table.configure_mock(put_item=mock_put_item)
        dynamodb_put_coupon({'key': 'value'})
        mock_put_item.assert_called_once_with({})

    # @mock.patch('dynamodb_coupons._dynamodb_coupons_table')
    # def test_dynamodb_put_coupon(self, mock_dynamodb_coupons_table):
    #     mock_put_item = MagicMock()
    #     mock_dynamodb_coupons_table.configure_mock(put_item=mock_put_item)
    #     dynamodb_put_coupon({'key': 'value'})
    #     mock_put_item.assert_called_once_with({})
