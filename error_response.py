def build_bad_request_response(message=None):
    return _build_response(400, message)


def _build_response(status_code, message):
    return {
        'statusCode': status_code,
        'body': {
            'message': message,
        },
    }


