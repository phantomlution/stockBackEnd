'''
    新闻内容采集
'''
from src.service.HtmlService import get_response, get_parsed_href_html
from src.utils.date import get_current_date_str, get_current_datetime_str, getCurrentTimestamp, date_str_to_timestamp
from bs4 import BeautifulSoup
import json
from functools import wraps
from src.service.StockService import StockService
from src.utils.date import get_ambiguous_date

client = StockService.getMongoInstance()
news_document = client.stock.news

source_config = {
    "cnbc": {
        "label": 'cnbc',
        "url": 'https://www.cnbc.com/world/?region=world'
    },
    'financial_times': {
        "label": 'financial_times',
        "url": 'https://cn.ft.com/'
    },
    "central_bank_communication": {
        "label": '中国央行-沟通交流',
        "homepage": 'http://www.stats.gov.cn/',
        "url": 'http://www.stats.gov.cn/tjsj/zxfb/index.html'
    },
    "foreign_affair": {
        "label": '外交部表态',
        "url": 'https://www.fmprc.gov.cn/web/fyrbt_673021/dhdw_673027/'
    },
    "development_revolution_committee": { # deprecated
        "label": '发改委',
        "url": 'http://www.ndrc.gov.cn/'
    },
    'prc_board_meeting': {
        "label": 'prc_board_meeting',
        "url": "http://www.12371.cn/special/zzjhy/"
    },
    'prc_collective_learning': {
        "label": 'prc_collective_learning',
        "url": 'http://www.12371.cn/special/lnzzjjtxx/'
    },
    'commerce_department_news_press': { # 商务部
        "label": 'commerce_department_news_press',
        "url": 'http://www.mofcom.gov.cn/article/ae/'
    }
}


def news_updator(func):
    @wraps(func)
    def update_news(*args, **kwargs):
        news_list = func(*args, **kwargs)

        for news in news_list:
            news["create_date"] = get_current_datetime_str()
            news["create_timestamp"] = getCurrentTimestamp()
            news["has_read"] = False
            if 'premium' not in news:
                news['premium'] = False
            if 'publish_date' not in news:
                news['publish_date'] = get_current_date_str()
            else:
                # check publish_date format
                date_str_to_timestamp(news['publish_date'])

            search_model = {
                "source": news['source'],
                "url": news['url']
            }
            if news_document.find_one(search_model) is None:
                news_document.update(search_model, news, True)
    return update_news


class NewsScratchWorker:

    def fix_date(self, date_str):
        separator = '-'
        date_item_list = date_str.split(separator)

        return date_item_list[0] + separator + ('0' if len(date_item_list[1]) == 1 else '') + date_item_list[1] + separator + ('0' if len(date_item_list[2]) == 1 else '') + date_item_list[2]

    @news_updator
    def get_cnbc_news(self):
        source = 'cnbc'
        url = source_config[source]['url']

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
                                "source": source,
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

                            url_path_list = model['url'].split('/')
                            year_index = 3
                            if url_path_list[year_index] == 'video':
                                year_index += 1
                            model['publish_date'] = url_path_list[year_index] + '-' + url_path_list[year_index + 1] + '-' + url_path_list[year_index + 2]

                            result.append(model)

        return result

    @news_updator
    def get_financial_times_news(self):
        source = 'financial_times'
        result = []
        url = source_config[source]['url']
        raw_html = get_response(url, use_proxy=True)
        parsed_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_html, 'html.parser')
        item_list = html.select('.item-container')
        for container_item in item_list:
            model = {
                "section": "",
                "source": source,
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
            if thumb_item is not None and 'data-url' in thumb_item:
                model['thumb'] = thumb_item['data-url']

            description_item = container_item.select_one(".item-lead")
            if description_item is not None:
                model['shorterDescription'] = description_item.text

            result.append(model)

        return result

    @news_updator
    def get_central_bank_communication_news(self):
        result = []
        source = 'central_bank_communication'
        url = source_config[source]['url']
        raw_html = get_response(url)
        parsed_raw_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_raw_html, 'html.parser')
        item_list = html.select(".center_list li")
        for item in item_list:
            # if 'class' in item:
            if 'class' in item.attrs and 'cont_line' in item.attrs['class']:
                continue
            if item.select_one(".fenye") is not None:
                continue

            title_element = item.select_one(".cont_tit03")
            date_element = item.select_one(".cont_tit02")
            href_element = item.select_one('a')
            model = {
                "source": source,
                "title": title_element.text,
                "publish_date": date_element.text,
                "url": href_element['href']
            }

            result.append(model)

        return result

    @news_updator
    def get_foreign_affair_news(self):
        result = []
        source = 'foreign_affair'
        url = source_config[source]['url']
        raw_html = get_response(url)
        parsed_raw_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_raw_html, 'html.parser')
        item_list = html.select('.rebox_news li')
        for item in item_list:
            href_element = item.select_one("a")
            date_element = list(item.children)[1]

            model = {
                "source": source,
                "title": href_element.text,
                "url": href_element['href'],
                "publish_date": str.strip(date_element[date_element.index('(') + 1:date_element.rindex(")")]),
            }

            result.append(model)

        return result

    @news_updator
    def get_development_revolution_committee_news(self):
        result = []
        source = 'development_revolution_committee'
        url = source_config[source]['url']
        raw_html = get_response(url)
        parsed_raw_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_raw_html, 'html.parser')
        gate_list = html.select('.mainCate')
        for gate in gate_list:
            gate_element = gate.select_one("h3")
            tab_container_list = gate.select('.tab_Contentbox > div')
            if tab_container_list is not None:
                for tab_container in tab_container_list:
                    tab_id = tab_container['id']
                    tab_label_id = tab_id[tab_id.index('_') + 1:]
                    tab_label_element = html.select_one("#"+ tab_label_id.replace('_', ''))
                    tab_label_text = tab_label_element.text
                    article_list = tab_container.select('li.li')
                    for article in article_list:
                        date_element = article.select_one("font")
                        publish_date = date_element.text.replace('/', '-')
                        if len(publish_date) == 0:
                            publish_date = get_current_date_str()
                        title_element = article.select_one('a')
                        model = {
                            "source": source,
                            "section": gate_element.text + '-' + tab_label_text,
                            "title": title_element.text,
                            "url": title_element['href'],
                            "publish_date": publish_date
                        }
                        result.append(model)

        return result

    @news_updator
    def get_prc_board_meeting_news(self):
        result = []
        source = 'prc_board_meeting'
        url = source_config[source]['url']
        raw_html = get_response(url)
        parsed_raw_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_raw_html, 'html.parser')
        article_container = html.select_one("ul.ul_list")
        article_list = article_container.select("li")
        for article in article_list[:5]:
            date_element = article.select_one("span")
            publish_date = date_element.text.replace('年', '-').replace('月', '-').replace('日', '')
            title_element = article.select_one("a")
            model = {
                "source": source,
                "publish_date": self.fix_date(publish_date),
                "title": title_element.text,
                "url": title_element['href']
            }
            result.append(model)

        return result

    @news_updator
    def get_prc_collective_learning_news(self):
        result = []
        source = 'prc_collective_learning'
        url = source_config[source]['url']
        raw_html = get_response(url)
        parsed_raw_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_raw_html, 'html.parser')
        article_container = html.select_one("#dyw640_right_list01")
        article_list = article_container.select(".list_cont")
        for article in article_list:
            section = article.select_one("h4").text
            model = {
                "source": source,
                "section": section,
                "url": article.select_one("a")['href']
            }

            date_split_list = model['url'].split('/')
            year_index = 3
            publish_date = date_split_list[year_index] + '-' + date_split_list[year_index + 1] + '-' + date_split_list[year_index + 2]
            model['publish_date'] = self.fix_date(publish_date)
            for li_item in article.select("ul li"):
                if '学习内容' in li_item.contents[0].text:
                    model['title'] = li_item.contents[1]
                elif '讲话主旨' in li_item.contents[0].text:
                    model['shorterDescription'] = li_item.contents[1]
            result.append(model)

        return result

    @news_updator
    def get_commerce_department_news_press_news(self):
        result = []
        source = 'commerce_department_news_press'
        url = source_config[source]['url']
        raw_html = get_response(url)
        parsed_raw_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_raw_html, 'html.parser')
        section_list = html.select('section.f-mt20')
        for section in section_list:
            section_name = section.select_one("header h3").text
            article_list = section.select('.u-newsList01 li')
            for article in article_list:
                title_item = article.select_one('a')
                date_item = article.select_one("span").text.replace('[', '').replace(']', '').split('-')
                month = int(date_item[0])
                day = int(date_item[1])
                release_date = get_ambiguous_date(month, day)
                result.append({
                    "source": source,
                    "title": title_item.text,
                    "section": section_name,
                    "url": title_item['href'],
                    "publish_date": release_date
                })
        return result





if __name__ == '__main__':
    # 重要的数据手动同步
    NewsScratchWorker().get_cnbc_news()
    NewsScratchWorker().get_financial_times_news()