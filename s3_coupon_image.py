import base64
import functools
import uuid

import boto3


def s3_put_coupon_image(encoded_image, image_name):
    image_s3_key = _build_s3_key('image', image_name)
    binary_image = base64.b64decode(encoded_image)
    return _s3_coupons_bucket().put_object(
        Key=image_s3_key,
        Body=binary_image,
    )


def _build_s3_key(directory, name):
    return f"{directory}/{str(uuid.uuid4())}/{name}"


@functools.lru_cache()
def _s3_coupons_bucket():
    return boto3.resource('s3').Bucket('shop-coupons-deliverer.coupons')
