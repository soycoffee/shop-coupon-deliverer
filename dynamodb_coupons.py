import functools

import boto3


def dynamodb_put_coupon(item):
    return _dynamodb_coupons_table().put_item(Item=item)


def dynamodb_get_coupon(_id):
    return _dynamodb_coupons_table().get_item(Key={'id': _id})


def dynamodb_scan_coupons():
    return _dynamodb_coupons_table().scan(Limit=100)


def dynamodb_delete_coupon(_id):
    return _dynamodb_coupons_table().delete_item(Key={'id': _id})


@functools.lru_cache()
def _dynamodb_coupons_table():
    return boto3.resource('dynamodb').Table('coupons')
