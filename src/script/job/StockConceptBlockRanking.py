'''
    获取概念板块每日排行榜
'''
from src.script.job.Job import Job
from src.service.StockService import StockService
from src.service.DataService import DataService

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
            history_data = DataService.get_concept_block_history(concept_code)
            for history_data_item in history_data:
                date_str = history_data_item['date']
                if date_str not in data_map:
                    data_map[date_str] = []
                history_data_item['name'] = concept_name
                history_data_item['code'] = concept_code
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
            concept_block_list = DataService.get_concept_block_item_list()

            first_round_data = self.get_concept_block_data(concept_block_list)

            # 为了对齐排行榜顺序，重新筛选有效的概念板块
            new_concept_block_list = []
            for item in first_round_data[0]['ranking']:
                new_concept_block_list.append({
                    "code": item['code'],
                    "name": item['name']
                })

            result = self.get_concept_block_data(new_concept_block_list)

            concept_block_ranking_document.drop()
            for ranking_item in result:
                ranking_length = len(ranking_item['ranking'])
                concept_block_list_length = len(new_concept_block_list)
                if ranking_length != concept_block_list_length:
                    print('{}/{}'.format(ranking_length, concept_block_list_length))
                    if concept_block_list_length - ranking_length > 1:
                        raise Exception('长度不一致')
                concept_block_ranking_document.save(ranking_item)
            task_id = task["id"]
            self.job.success(task_id)


if __name__ == '__main__':
    StockConceptBlockRanking().run()