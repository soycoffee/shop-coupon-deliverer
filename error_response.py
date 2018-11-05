def build_bad_request_response(*messages):
    return _build_response(400, messages)


def build_not_found_response(*message):
    return _build_response(404, message)


def _build_response(status_code, messages):
    return {
        'statusCode': status_code,
        'body': {
            'messages': messages,
        },
    }


