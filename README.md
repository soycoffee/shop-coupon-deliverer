# システム構成図

[INFRASTRUCTURE_DIAGRAM.png](INFRASTRUCTURE_DIAGRAM.png)

# Base URL

https://3h4ksa28ci.execute-api.ap-northeast-1.amazonaws.com/default

# Action

API Gateway からアクセスする。  
常に Request Headers に `x-api-key` を含める。  

## Query Coupons

#### Access
`GET /`

#### Request Headers
* `Last-Evaluated-Key`:  
  2ページ目以降を取得するために必要。  
  前ページの Response Headers から `Last-Evaluated-Key` をそのまま利用する。  

#### Response Headers
* `Last-Evaluated-Key`:  
  次ページの取得に利用する。  
  以降のページが存在しない場合、 Headers に含まれない。  

#### Response Body (Example)
```json
[
  {
    "id": "0000001",
    "title": "全商品 10% OFF！",
    "description": "ご利用一回限り。他のクーポンとの併用はできません。クーポンをご利用いただいた場合、ポイントはつきません。",
    "image_s3_key": "image/XXXX",
    "qr_code_image_s3_key": "qr_code_image/XXXX",
    "image_url": "https://s3.ap-northeast-1.amazonaws.com/shop-coupon-deliverer.coupons/image/XXXX",
    "qr_code_image_url": "https://s3.ap-northeast-1.amazonaws.com/shop-coupon-deliverer.coupons/qr_code_image/XXXX"
  }
]
```
最大20件のクーポンを返す。  
21件目以降の取得には `Last-Evaluated-Key` を利用する。  

## Read Coupon

#### Access
`GET /:id`

#### Response Body (Example)
```json
{
  "id": "0000001",
  "title": "全商品 10% OFF！",
  "description": "ご利用一回限り。他のクーポンとの併用はできません。クーポンをご利用いただいた場合、ポイントはつきません。",
  "image_s3_key": "image/XXXX",
  "qr_code_image_s3_key": "qr_code_image/XXXX",
  "image_url": "https://s3.ap-northeast-1.amazonaws.com/shop-coupon-deliverer.coupons/image/XXXX",
  "qr_code_image_url": "https://s3.ap-northeast-1.amazonaws.com/shop-coupon-deliverer.coupons/qr_code_image/XXXX"
}
```

## Create Coupon

#### Access
`POST /`

#### Request Body (Example)
```json
{
  "title": "全商品 10% OFF！",
  "description": "ご利用一回限り。他のクーポンとの併用はできません。クーポンをご利用いただいた場合、ポイントはつきません。",
  "image": "data:image/png;base64,XXXX",
  "qr_code_image": "data:image/png;base64,XXXX"
}
```
`image`, `qr_code_image` は画像の Data URI とする。

#### Response Body (Example)
```json
{
  "id": "0000001",
  "title": "全商品 10% OFF！",
  "description": "ご利用一回限り。他のクーポンとの併用はできません。クーポンをご利用いただいた場合、ポイントはつきません。",
  "image_s3_key": "image/19afcda7-0ac6-49b6-8327-b8fb9adb277f",
  "qr_code_image_s3_key": "qr_code_image/099a2390-e012-422e-af63-aa448777b86b"
}
```

## Update Coupon

#### Access
`PUT /:id`

#### Request Body (Example)
*Create Coupon* と同様なので、省略する。

#### Response Body (Example)
*Create Coupon* と同様なので、省略する。

## Delete Coupon

#### Access
`DELETE /:id`

