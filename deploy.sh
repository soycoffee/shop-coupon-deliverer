git archive HEAD --output=lambda.zip
aws lambda create-function --function-name=shop-coupon-deliverer --zipfile=lambda.zip
