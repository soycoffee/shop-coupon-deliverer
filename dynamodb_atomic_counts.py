import functools

import boto3


def dynamodb_increment_atomic_count(key):
    return int(_dynamodb_atomic_counts_table().update_item(
        Key={'key': key},
        UpdateExpression='set current_number = current_number + :increment',
        ExpressionAttributeValues={':increment': 1},
        ReturnValues='UPDATED_NEW',
    )['Attributes']['current_number'])


def dynamodb_get_atomic_count(key):
    return int(_dynamodb_atomic_counts_table().get_item(Key={'key': key})['Item']['current_number'])


@functools.lru_cache()
def _dynamodb_atomic_counts_table():
    return boto3.resource('dynamodb').Table('atomic_counts')
