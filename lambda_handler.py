from datetime import datetime

from dynamodb_coupon import dynamodb_put_coupon
from s3_coupon_image import s3_put_coupon_image


def lambda_handler(event, context):
    coupon_image_object = s3_put_coupon_image(event['image'], event['image_name'])
    coupon_object = dynamodb_put_coupon({
        'id': datetime.now().isoformat(),
        'image_s3_key': coupon_image_object.key,
    })
    return coupon_object

