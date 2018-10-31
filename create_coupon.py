from dynamodb_atomic_counts import dynamodb_atomic_count
from dynamodb_coupons import dynamodb_put_coupon
from s3_coupon_image import s3_put_coupon_image


def create_coupon(image, image_name):
    image_object = s3_put_coupon_image(image, image_name)
    _id = str(dynamodb_atomic_count('coupon_id'))
    return dynamodb_put_coupon({
        'id': _id,
        'image_s3_key': image_object.key,
    })

