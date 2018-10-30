from datetime import datetime

from dynamodb_coupon import dynamodb_put_coupon
from s3_coupon_image import s3_put_coupon_image


def create_coupon(image, image_name):
    coupon_image_object = s3_put_coupon_image(image, image_name)
    return dynamodb_put_coupon({
        'id': datetime.now().isoformat(),
        'image_s3_key': coupon_image_object.key,
    })

