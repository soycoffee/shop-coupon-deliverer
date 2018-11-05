git archive HEAD --output=lambda.zip
aws lambda update-function-code --function-name=shop-coupon-deliverer --zip-file=fileb://lambda.zip
