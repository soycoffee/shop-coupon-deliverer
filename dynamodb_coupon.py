import functools

import boto3


def dynamodb_put_coupon(item):
    return _dynamo_coupons_table().put_item(
        Item=item,
    )


@functools.lru_cache()
def _dynamo_coupons_table():
    return boto3.resource('dynamodb').Table('coupons')
