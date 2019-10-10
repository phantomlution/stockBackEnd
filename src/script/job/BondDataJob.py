'''
    同步债券发行数据
'''
import json
from src.utils.date import time_format, get_split_range
from bs4 import BeautifulSoup
from src.utils.extractor import Extractor
import time
from src.service.StockService import StockService
import datetime
from src.utils.sessions import FuturesSession
session = FuturesSession(max_workers=1)

client = StockService.getMongoInstance()
sync_document = client.stock.sync
bond_document = client.stock.bond

class BondDataJob:

    def __init__(self):
        #  同步数据间隔的天数
        self.sync_duration = 2
        self.sync_table_key = 'bond_data'
        # 债券类型列表
        self.bond_type_list = [ # 同业存单数据量大概占了 80%
            # {
            #     "valueName": "1",
            #     "tabShrtNm": "",
            #     "tabName": "同业存单",
            #     "typeSrno": "100041"
            # },
            # {
            #     "valueName": "3",
            #     "tabShrtNm": "",
            #     "tabName": "国债",
            #     "typeSrno": "100001"
            # },
            {
                "valueName": "5",
                "tabShrtNm": "",
                "tabName": "地方政府债",
                "typeSrno": "100011"
            }, {
                "valueName": "15",
                "tabShrtNm": "",
                "tabName": "政策性金融债",
                "typeSrno": "100003"
            }, {
                "valueName": "17",
                "tabShrtNm": "",
                "tabName": "二级资本工具",
                "typeSrno": "100054,100005"
            }, {
                "valueName": "50",
                "tabShrtNm": "",
                "tabName": "普通金融债",
                "typeSrno": "100007"
            }, {
                "valueName": "52",
                "tabShrtNm": "",
                "tabName": "证券公司短期融资券",
                "typeSrno": "100024"
            }, {
                "valueName": "60",
                "tabShrtNm": "",
                "tabName": "资产支持证券",
                "typeSrno": "999999"
            }, {
                "valueName": "63",
                "tabShrtNm": "",
                "tabName": "政府支持机构债券",
                "typeSrno": "100027"
            }, {
                "valueName": "64",
                "tabShrtNm": "",
                "tabName": "短期融资券",
                "typeSrno": "100006"
            }, {
                "valueName": "65",
                "tabShrtNm": "",
                "tabName": "中期票据",
                "typeSrno": "100010"
            }, {
                "valueName": "70",
                "tabShrtNm": "",
                "tabName": "超短期融资券",
                "typeSrno": "100029"
            }, {
                "valueName": "80",
                "tabShrtNm": "",
                "tabName": "企业债",
                "typeSrno": "100004"
            }, {
                "valueName": "90",
                "tabShrtNm": "",
                "tabName": "保险公司资本补充债",
                "typeSrno": "100056"
            }, {
                "valueName": "110",
                "tabShrtNm": "",
                "tabName": "项目收益债券",
                "typeSrno": "100057"
            }, {
                "valueName": "140",
                "tabShrtNm": "",
                "tabName": "资产支持票据",
                "typeSrno": "100072"
            }, {
                "valueName": "150",
                "tabShrtNm": "",
                "tabName": "绿色债务融资工具",
                "typeSrno": "100073"
            }, {
                "valueName": "180",
                "tabShrtNm": "",
                "tabName": "非公开定向债务融资工具",
                "typeSrno": "100050"
            }
        ]

    def load_bond(self, bond_no, start, end, page_no=1, page_size=30):
        url = 'http://www.chinamoney.com.cn/ags/ms/cm-u-notice-issue/clinrAnNotice'
        params = {
            "channelId": 2561,
            "bondSrno": bond_no,
            "drftClAngl": "07",
            "scnd": "0701",
            "pageNo": page_no,
            "pageSize": page_size,
            "startDate": start,
            "endDate": end,
            "limit": 1,
            "timeln": 1,
        }

        return json.loads(session.get(url, params=params).result().content)

    def get_html(self, url):
        headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36"
        }

        response = session.get(url, headers=headers)
        return response.result().content.decode()

    # 强制校验对应的列名，以防产生赞数据
    def assert_field_name(self, data, name, default=None):
        target_row = -1
        target_column = - 1
        for rowIndex, row in enumerate(data):
            if target_row != -1:
                break

            if type(row) is not list:
                continue

            for columnIndex, column in enumerate(row):
                field_name = column
                if name in str.strip(field_name):
                    target_row = rowIndex
                    target_column = columnIndex
                    break

        if target_row == -1:
            if default is None:
                print(data)
                print(name)
                raise Exception('数据错位')
            else:
                return default
        else:
            value = data[target_row][target_column + 1] + ''
            return str.strip(value)


    # 获取完整的数据，由分页数据拼接而成
    def get_total_data(self, bond_no, start, end):
        return_result = []
        init_data = self.load_bond(bond_no, start, end)
        page_count = init_data['data']['pageTotalSize']
        for page_number in range(1, page_count + 1):
            print('{}/{}'.format(page_number, page_count))
            page = self.load_bond(bond_no, start, end, page_number)
            for record in page['records']:
                url = 'http://www.chinamoney.com.cn' + record['draftPath']
                raw_html = self.get_html(url)
                html = BeautifulSoup(raw_html, 'html.parser')
                table_doc = html.select_one('table')
                if table_doc is None:
                    data = None

                else:
                    extractor = Extractor(table_doc)
                    extractor.parse()
                    raw_data = extractor.return_list()
                    data = {
                        "title": str.strip(raw_data[0][0]),
                        "continuous": '续发行' in str(raw_data),
                        "name": self.assert_field_name(raw_data, '证券名称'),
                        "brief_name": self.assert_field_name(raw_data, '证券简称'),
                        "code": self.assert_field_name(raw_data, '证券代码'),
                        "publish_company": self.assert_field_name(raw_data, '发行人'),
                        'publish_amount': self.assert_field_name(raw_data, '发行总额（亿元）'),
                        'interest_rate_type': self.assert_field_name(raw_data, '计息方式'),
                        'pay_interest_duration': self.assert_field_name(raw_data, '付息频率'),
                        'issue_start': self.assert_field_name(raw_data, '上市流通日'),
                        'issue_end': self.assert_field_name(raw_data, '交易流通终止日'),
                        'start_interest_date': self.assert_field_name(raw_data, '起息日', default=''),
                        'pay_back_date': self.assert_field_name(raw_data, '兑付日', default='')
                    }

                record['data'] = data
                return_result.append(record)

        return return_result


    def sync_data(self):
        sync_model = sync_document.find_one({"key": self.sync_table_key})
        if sync_model is None:
            last_update = '2017-01-01'
        else:
            last_update = sync_model['last_update']

        # 开始同步数据
        current = datetime.datetime.now().strftime(time_format)
        split_range_list = get_split_range(last_update, current, self.sync_duration)
        for split_range in split_range_list:
            # 按照指定区间同步数据
            for bond_type in self.bond_type_list:
                total_data = self.get_total_data(bond_type['typeSrno'], split_range['start'], split_range['end'])
                for item in total_data:
                    item['bond_type'] = bond_type['typeSrno']
                    item['bond_type_name'] = bond_type['tabName']
                    bond_document.update({ "contentId": item["contentId"]}, item, True)

            # 更新进度表
            sync_document.update({ "key": self.sync_table_key}, {
                "key": self.sync_table_key,
                "last_update": split_range['end']
            }, True)
            time.sleep(0.3)
            print('at {}'.format(split_range['end']))


if __name__ == '__main__':
    BondDataJob().sync_data()