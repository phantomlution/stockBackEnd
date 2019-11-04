'''
    新闻内容采集
'''
from src.service.HtmlService import get_response, get_parsed_href_html
from src.utils.date import get_current_datetime_str, getCurrentTimestamp
from bs4 import BeautifulSoup
import json
from src.service.StockService import StockService


client = StockService.getMongoInstance()
news_document = client.stock.news


class NewsScratchJob:
    def get_cnbc_news(self):
        url = 'https://www.cnbc.com/world/?region=world'

        raw_response = get_response(url)
        raw_response = raw_response.split('window.__s_data')[1]
        raw_response = raw_response[raw_response.index('{'):]
        raw_response = raw_response[:raw_response.index('window.__c_data')]
        raw_response = raw_response[:raw_response.rindex(';')]

        model = json.loads(raw_response)

        result = []
        page = model['page']['page']
        for layout in page['layout']:
            for columns in layout['columns']:
                for module in columns['modules']:
                    module_data = module['data']
                    if 'assets' in module_data:
                        assets = module_data['assets']
                        for item in assets:
                            model = {
                                "premium": False,
                                "source": 'CNBC',
                                "title": item['title'],
                                "url": item['url'],
                                'shorterDescription': '',
                                'section': '',
                                "materialType": '',
                                'thumb': ''
                            }

                            if 'shorterHeadline' in item or 'shorterDescription' in item:
                                model['shorterDescription'] = item['shorterHeadline'] if 'shorterHeadline' in item else item['shorterDescription']

                            if 'section' in item:
                                section = item['section']
                                if 'eyebrow' in section:
                                    model['section'] = section['eyebrow']
                                elif 'tagName' in section:
                                    model['section'] = section['tagName']

                            if 'premium' in item and item['premium']:
                                model['premium'] = True
                            if 'type' in item and item['type'] == 'cnbcvideo':
                                model['materialType'] = 'video'

                            if 'promoImage' in item:
                                model['thumb'] = item['promoImage']['url']

                            result.append(model)

        return result

    def update_news(self, news_list):
        for news in news_list:
            news["update_date"] = get_current_datetime_str()
            news["update_timestamp"] = getCurrentTimestamp()
            search_model = {
                "source": news['source'],
                "url": news['url']
            }
            if news_document.find_one(search_model) is None:
                news_document.update(search_model, news, True)

    def get_financial_times_news(self):
        result = []
        url = 'https://cn.ft.com/'
        raw_html = get_response(url, use_proxy=True)
        parsed_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_html, 'html.parser')
        item_list = html.select('.item-container')
        for container_item in item_list:
            model = {
                "section": "",
                "source": "FinancialTimes",
                "premium": False,
                "shorterDescription": ""
            }

            tag_item = container_item.select_one('.item-tag')
            if tag_item is not None:
                model['section'] = tag_item.text

            head_item = container_item.select_one(".item-headline > a")
            model['title'] = head_item.text
            model['url'] = head_item['href']
            if 'premium' in model['url'].split('/'):
                model['premium'] = True

            thumb_item = container_item.select_one("figure")
            if thumb_item is not None:
                model['thumb'] = thumb_item['data-url']

            description_item = container_item.select_one(".item-lead")
            if description_item is not None:
                model['shorterDescription'] = description_item.text

            result.append(model)

        return result

    def update_cnbc_news(self):
        news_list = self.get_cnbc_news()
        self.update_news(news_list)

    def update_financial_times_news(self):
        news_list = self.get_financial_times_news()
        self.update_news(news_list)


if __name__ == '__main__':
    NewsScratchJob().update_cnbc_news()
    NewsScratchJob().update_financial_times_news()