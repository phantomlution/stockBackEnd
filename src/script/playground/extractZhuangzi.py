# 提取《庄子》全文，并重新排版
from src.service.HtmlService import get_response
from bs4 import BeautifulSoup
from src.utils.FileUtils import generate_static_dir_file
import os
import json


class Extractor:
    def __init__(self):
        self.content_list = []
        self.content_cache = None
        self.last_paragraph = None

    def flush_last_paragraph(self):
        if self.last_paragraph is None:
            return
        if len(self.last_paragraph['label']) != 0:
            if len(self.last_paragraph['content']) == 0:
                raise Exception('content is empty')
            # flush content
            self.content_cache['paragraph'].append(self.last_paragraph)

    def flush_content(self):
        # flush cache
        if self.content_cache is not None:
            self.content_list.append(self.content_cache)

    def get_html(self):
        url = 'http://m.fosss.org/book/zhuangzi/index.html'
        raw_html = get_response(url)
        html = BeautifulSoup(raw_html, 'html.parser')
        return html

    def get_flatten_children_list(self, html):
        # 展开所有的子项, 最多展开一项
        result = []
        paragraph_list = html.select_one("#mainContent").children
        for paragraph in paragraph_list:
            local = {
                'can_expand': False
            }
            if hasattr(paragraph, 'children') and len(list(paragraph.children)) > 1:
                for sub_paragraph in paragraph.children:
                    if sub_paragraph.name == 'p':
                        local['can_expand'] = True
                        break
            if local['can_expand']:
                for sub_paragraph in paragraph.children:
                    result.append(sub_paragraph)
            else:
                result.append(paragraph)

        return result

    def check_integrity(self):
        label_set = ['题解', '原文', '注释', '译文']
        for content in self.content_list:
            if (len(content['paragraph']) - 1) % 3 != 0 and (len(content['paragraph']) - 1) % 2 != 0:
                raise Exception('顺序错误')
            for idx, paragraph in enumerate(content['paragraph']):
                label = paragraph['label']
                if label not in label_set:
                    raise Exception('exists extra label')

                if idx == 0:
                    if label != '题解':
                        raise Exception('题解')

    def reformat(self):
        result = []
        for content in self.content_list:
            description = content['paragraph'][0]
            if description['label'] != '题解':
                raise Exception('序列错误')
            content_paragraph_list = content['paragraph'][1:]

            model = {
                "title": content['title'],
                "description": description['content'],
                "paragraph": []
            }
            paragraph_cache = []
            for content_paragraph in content_paragraph_list:
                if content_paragraph['label'] == '原文' and len(paragraph_cache) > 0:
                    # flush content
                    paragraph_model = {
                        "raw": [],
                        "notes": [],
                        "translation": []
                    }
                    for item in paragraph_cache:
                        paragraph_title = item['label']
                        if paragraph_title == '原文':
                            field = 'raw'
                        elif paragraph_title == '译文':
                            field = 'translation'
                        elif paragraph_title == '注释':
                            field = 'notes'
                        else:
                            raise Exception('field not exists')
                        if len(paragraph_model[field]) > 0:
                            raise Exception('数据重叠')
                        if field == 'notes' and len(item['content']) == 1:
                            paragraph_model[field] = str.strip(item['content'][0]).split('\n')
                        else:
                            paragraph_model[field] = item['content']

                    paragraph_cache.clear()
                    model['paragraph'].append(paragraph_model)
                paragraph_cache.append(content_paragraph)
            result.append(model)
        return result

    def run(self):
        html = self.get_html()
        paragraph_list = self.get_flatten_children_list(html)
        for item in paragraph_list:
            if item.name is not None:
                tag_name = item.name
                if tag_name == 'h2':
                    self.flush_last_paragraph()
                    self.flush_content()

                    self.content_cache = {
                        "title": str.strip(item.text.replace('▲', '')),
                        "paragraph": []
                    }
                    self.last_paragraph = None
                    continue
                if self.content_cache is not None and len(self.content_cache['title']) > 0:
                    inner_text = str.strip(item.text.replace('▲', ''))
                    if len(inner_text) == 0:
                        continue
                    # 修正缺失的符号
                    if inner_text[2] == '】':
                        inner_text = '【' + inner_text

                    if inner_text[0] == '【' and inner_text[-1] == '】':
                        self.flush_last_paragraph()
                        self.last_paragraph = {
                            'label': inner_text[1:-1],
                            "content": []
                        }
                        continue
                    elif inner_text[0] == '【' and inner_text[3] == '】':
                        # 修复异常数据
                        self.flush_last_paragraph()
                        self.last_paragraph = {
                            'label': inner_text[1:3],
                            "content": []
                        }
                        self.last_paragraph['content'].append(inner_text[4:])
                        continue
                    if len(self.last_paragraph['label']) > 0:
                        # append paragraph
                        self.last_paragraph['content'].append(item.text)
        # check sequence and integrity, and reformat text
        self.check_integrity()
        article_list = self.reformat()

        # check article list
        table_list = html.select("table")
        content_table = table_list[1].select("li")
        for idx, article in enumerate(article_list):
            if article['title'] not in content_table[idx].text:
                raise Exception('标题错误')

        # generate file
        file_dir = 'zhuangzi' + os.sep
        generate_static_dir_file(file_dir + 'raw.json', json.dumps(article_list, ensure_ascii=False))
        article_content = ''
        for idx, article in enumerate(article_list):
            article_content += ('' if idx == 0 else '\n\n\n\n' ) + '# ' + article['title'] + '\n\n'
            for paragraph in article['paragraph']:
                article_content += '\n\n'.join(paragraph['translation'])

        generate_static_dir_file(file_dir + 'zhuangzi.txt', article_content)


if __name__ == '__main__':
    Extractor().run()









