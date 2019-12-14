import json


def list_to_str(_list):
    separator = '\n'
    result = ''
    for idx, item in enumerate(_list):
        result = result + (separator if idx > 0 else '') + json.dumps(item, ensure_ascii=False)

    return result
