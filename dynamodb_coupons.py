import functools

import boto3
from boto3.dynamodb.conditions import Key


def dynamodb_put_coupon(item):
    return _dynamodb_coupons_table().put_item(Item=item)


def dynamodb_get_coupon(_id):
    return _dynamodb_coupons_table().get_item(Key={'id': _id})


def dynamodb_query_coupons(page):
    return _dynamodb_coupons_table().query(
        IndexName='page-id-index',
        KeyConditionExpression=Key('page').eq(page),
    )


def dynamodb_delete_coupon(_id):
    return _dynamodb_coupons_table().delete_item(Key={'id': _id})


@functools.lru_cache()
def _dynamodb_coupons_table():
    return boto3.resource('dynamodb').Table('coupons')
