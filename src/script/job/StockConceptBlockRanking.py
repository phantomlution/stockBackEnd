'''
    获取概念板块每日排行榜
'''
from src.script.job.Job import Job
from src.service.StockService import StockService
from src.service.DataWorker import DataWorker
from src.service.EastMoneyWorker import EastMoneyWorker

client = StockService.getMongoInstance()
concept_block_ranking_document = client.stock.concept_block_ranking


class StockConceptBlockRanking:
    def __init__(self):
        self.job = Job(name='概念板块每日排行榜')
        self.job.add({})

    def run(self, end_func=None):
        self.job.start(self.start, end_func)

    def get_concept_block_data(self, concept_block_list):
        data_map = {}
        # 提取板块数据
        for concept_block in concept_block_list:
            concept_code = concept_block['code']
            concept_name = concept_block['name']
            concept_url = concept_block['url']
            history_data = EastMoneyWorker.get_kline('90.' + concept_code)
            for history_data_item in history_data:
                history_data_item['percent'] = round((history_data_item['close'] - history_data_item['pre_close']) / history_data_item['pre_close'] * 100, 2)
                date_str = history_data_item['date']
                if date_str not in data_map:
                    data_map[date_str] = []
                history_data_item['name'] = concept_name
                history_data_item['code'] = concept_code
                history_data_item["url"] = concept_url
                data_map[date_str].append(history_data_item)
        result = []
        for date in data_map:
            result.append({
                "date": date,
                "ranking": sorted(data_map[date], key=lambda ranking: ranking['percent'], reverse=True)
            })

        result = sorted(result, key=lambda item: item['date'])

        return result

    def start(self):
        for task in self.job.task_list:
            # 获取概念板块
            concept_block_list = DataWorker.get_concept_block_item_list()

            result = self.get_concept_block_data(concept_block_list)

            concept_block_ranking_document.drop()
            for ranking_item in result:
                concept_block_ranking_document.save(ranking_item)
            task_id = task["id"]
            self.job.success(task_id)


if __name__ == '__main__':
    StockConceptBlockRanking().run()