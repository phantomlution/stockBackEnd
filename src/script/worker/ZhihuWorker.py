from src.service.HtmlService import get_response, get_parsed_href_html
from bs4 import BeautifulSoup
import json
from src.service.NotificationService import NotificationService


class ZhihuWorker:

    @staticmethod
    def get_user_list():
        return [
            'Jasonbugui'
        ]

    @staticmethod
    def resolve_content(raw):
        if isinstance(raw, list):
            result = ''
            for item in raw:
                if 'content' in item:
                    result += item['content']
                elif item['type'] == 'image':
                    result += '<div><img style="width:{width}px;height:{height}px" src="{src}"</div>'.format(width=item['width'], height=item['height'], src=item['url'])
            return result
        else:
            return str(raw)

    @staticmethod
    def get_activities(user_name):
        url = "https://www.zhihu.com/people/" + user_name + "/activities"

        raw_html = get_response(url)
        parsed_html = get_parsed_href_html(url, raw_html)
        html = BeautifulSoup(parsed_html, 'html.parser')
        page_json_script = html.select_one("#js-initialData")
        page_json = json.loads(page_json_script.text)
        entities_data = page_json['initialState']['entities']
        entities_activity = entities_data['activities']
        user_name_str = entities_data['users'][user_name]['name']

        for item_id in entities_activity:
            item = entities_activity[item_id]
            model = {
                "source": 'zhihu',
                "user_name": user_name_str,
                "action_text": item['actionText'],
                "schema": str(item['target']['schema']),
                "target_id": str(item['target']['id'])
            }
            model['id'] = model['source'] + '_' + model['target_id']
            schema = model['schema']
            if schema not in ['answer', 'pin', 'question', 'article']:
                print(item)
                raise Exception('类型异常:{}'.format(schema))

            target = entities_data[model['schema'] + 's'][model['target_id']]
            if schema == 'answer' or schema == 'pin' or schema == 'article':
                model['content'] = ZhihuWorker.resolve_content(target['content'])

            if schema == 'question':
                model['title'] = target['title']
                model['title_url'] = target['url']

            NotificationService.add(model['source'], {
                "title": '【知乎】关注更新',
                "description": user_name_str + ' ' + model['action_text'],
                "type": 'reader',
                "raw": model
            })

    @staticmethod
    def track_all_users():
        for user_name in ZhihuWorker.get_user_list():
            ZhihuWorker.get_activities(user_name)


if __name__ == '__main__':
    ZhihuWorker.track_all_users()
