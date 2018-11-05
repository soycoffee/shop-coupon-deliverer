import base64
import functools

import boto3


def s3_put_coupon_image(key, encoded_image):
    binary_image = base64.b64decode(encoded_image)
    return _s3_coupons_bucket().put_object(Key=key, Body=binary_image)


def s3_delete_coupon_image(key):
    return _s3_coupons_bucket().delete_objects(Delete={'Objects': [{'Key': key}]})


def s3_generate_coupon_url(key):
    return _s3_client().generate_presigned_url(
        ClientMethod='get_object',
        HttpMethod='GET',
        ExpiresIn=3600,
        Params={
            'Bucket': 'shop-coupon-deliverer.coupons',
            'Key': key,
        }
    )


@functools.lru_cache()
def _s3_client():
    return boto3.client('s3')


@functools.lru_cache()
def _s3_coupons_bucket():
    return boto3.resource('s3').Bucket('shop-coupon-deliverer.coupons')

