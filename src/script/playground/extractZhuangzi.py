# 提取《庄子》全文，并重新排版
from src.service.HtmlService import get_response
from bs4 import BeautifulSoup


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

    def run(self):
        url = 'http://m.fosss.org/book/zhuangzi/index.html'
        raw_html = get_response(url)
        html = BeautifulSoup(raw_html, 'html.parser')
        table_list = html.select("table")
        content_table = table_list[1]
        paragraph_list = html.select_one("#mainContent").children
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
                    if inner_text[0] == '【' and inner_text[-1] == '】':
                        self.flush_last_paragraph()
                        self.last_paragraph = {
                            'label': inner_text[1:-1],
                            "content": []
                        }
                        continue
                    if len(self.last_paragraph['label']) > 0:
                        # append paragraph
                        self.last_paragraph['content'].append(item.text)
        print(self.content_list)

        # TODO check sequence and integrity


if __name__ == '__main__':
    Extractor().run()









