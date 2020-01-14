'''
    数据处理函数
'''


class DataUtils:

    # 追加 pre_close
    @staticmethod
    def generate_pre_close(kline_list):
        for idx, item in enumerate(kline_list):
            if 'pre_close' in item and item['pre_close'] is not None:
                continue
            if idx == 0:
                item['pre_close'] = item['open']
            else:
                item['pre_close'] = kline_list[idx - 1]['close']