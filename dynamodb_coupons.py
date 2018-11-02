import functools

import boto3
from boto3.dynamodb.conditions import Attr


def dynamodb_put_coupon(item):
    return _dynamodb_coupons_table().put_item(
        Item=item,
        ConditionExpression=Attr('title').lte(20),
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
