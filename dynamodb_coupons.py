import functools

import boto3


def dynamodb_put_coupon(item):
    return _dynamodb_coupons_table().put_item(
        Item=item,
    )


def dynamodb_get_coupon(_id):
    return _dynamodb_coupons_table().get_item(
        Key={
            'id': _id,
        }
    )['Item']


@functools.lru_cache()
def _dynamodb_coupons_table():
    return boto3.resource('dynamodb').Table('coupons')
