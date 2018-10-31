import functools

import boto3


def dynamodb_put_coupon(item):
    return _dynamodb_coupons_table().put_item(
        Item=item,
    )


@functools.lru_cache()
def _dynamodb_coupons_table():
    return boto3.resource('dynamodb').Table('coupons')
