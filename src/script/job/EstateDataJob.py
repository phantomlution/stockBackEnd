'''
    抓取贝壳网的数据进行简单分析
'''
from src.service.HtmlService import get_response, extract_jsonp
from bs4 import BeautifulSoup
from src.service.StockService import StockService
from src.utils.date import get_current_date_str
import time
client = StockService.getMongoInstance()
estate_document = client.stock.estate
sync_document = client.stock.sync


class EstateDataJob:

    # 获取省份信息
    def extract_province_json(self):
        url = 'https://ajax.api.ke.com//config/cityConfig/getConfig'
        params = {
            "callback": "jQuery111106533390627398656_1570189217838",
            "type": "province",
            "category": "1"
        }
        response = get_response(url, params=params)
        data = extract_jsonp(response, params['callback'])

        province_list = []
        province_map = data['data']
        for province_id in province_map:
            province_list.append(province_map[province_id])

        return province_list

    def extract_city_json(self):
        city_map = {}
        url = 'https://www.ke.com/city/'
        raw_html = get_response(url)
        html = BeautifulSoup(raw_html, 'html.parser')
        province_html_list = html.select(".city_province")
        for province_html in province_html_list:
            province_name = str.strip(province_html.select_one('.city_list_tit').text)
            city_html_list = province_html.select('li')
            city_list = []
            for city_html in city_html_list:
                city_name = city_html.text
                city_url = city_html.select_one("a")['href']
                # 只考虑国内数据
                if 'i.ke.com' not in city_url:
                    city_py = city_url.split('//')[-1].split('.')[0]
                    city_list.append({
                        "name": city_name,
                        "url": city_url,
                        "py": city_py
                    })

            city_map[province_name] = city_list

        return city_map

    def get_province_city_json(self):
        province_json = self.extract_province_json()
        city_map = self.extract_city_json()
        for province in province_json:
            province_name = province['province_name']
            province['city_list'] = city_map[province_name]
            if len(province['city_list']) == 0:
                raise Exception('{}数据不完整'.format(province_name))

        return province_json

    # 目前先只提取城市的数值，如果有必要，通过累加区的信息来累加获得市的数据
    def extract_city_data(self, url):
        raw_html = get_response(url)
        html = BeautifulSoup(raw_html, 'html.parser')
        try:
            count_element = html.select_one(".resultDes .total span")
            if count_element is None:
                count_element = html.select_one('.resblock-have-find .value')
            count = str.strip(count_element.text)
        except Exception as e:
            print(url)
        return count

    def get_city_data(self, city):
        # 满两年url
        base_url = 'https:' + city['url'] + '/ershoufang'
        two_year_url = base_url + '/ty1/'
        five_year_url = base_url + '/mw1/'

        total_count = int(self.extract_city_data(base_url))
        two_year_count = int(self.extract_city_data(two_year_url))
        five_year_count = int(self.extract_city_data(five_year_url))

        return {
            "total": total_count,
            "less_than_two_year": total_count - two_year_count - five_year_count,
            'two_year': two_year_count,
            'five_year': five_year_count
        }

    def get_all_data(self):
        try:
            current_date = get_current_date_str()
            sync_key = 'estate_' + current_date

            progress = sync_document.find_one({ "key": sync_key })

            province_city_list = self.get_province_city_json()
            if progress is None:
                progress = {
                    "key": sync_key,
                    "province_name": province_city_list[0]['province_name'],
                    "done": False
                }
            if progress['done']:
                return

            started = False

            for idx, province in enumerate(province_city_list):
                province_name = province['province_name']
                # 定位到上一次的位置
                if started is False:
                    if province_name != progress['province_name']:
                        continue
                    else:
                        started = True

                progress['province_name'] = province_name
                sync_document.update({"key": sync_key}, progress, True)

                print('progress:{}/{}'.format(idx + 1, len(province_city_list)))

                for city in province['city_list']:
                    city['estate'] = self.get_city_data(city)
                    print(city['name'])
                    time.sleep(0.3)

                model = {
                    "province_name": province_name,
                    "date": current_date,
                    "data": province['city_list']
                }
                estate_document.update({ "province_name": province_name, "date": current_date }, model, True)
                time.sleep(1)
            progress['done'] = True
            sync_document.update({ "key": sync_key}, progress, True)
        except Exception as e:
            time.sleep(1)
            self.get_all_data()




if __name__ == '__main__':
    EstateDataJob().get_all_data()