

class lodash:

    @staticmethod
    def max_by(_list, _func):
        if len(_list) == 0:
            return None
        max_item = _list[0]
        for item in _list:
            if _func(item) > _func(max_item):
                max_item = item

        return max_item

    @staticmethod
    def min_by(_list, _func):
        if len(_list) == 0:
            return None
        min_item = _list[0]
        for item in _list:
            if _func(item) < _func(min_item):
                min_item = item

        return min_item

    @staticmethod
    def diff_in_percent(num1, num2, precision=2):
        return round((num1 - num2) / num2 * 100, precision)

    @staticmethod
    def find_index(_list, callback):
        for idx, item in enumerate(_list):
            if callback(item):
                return idx

        return -1