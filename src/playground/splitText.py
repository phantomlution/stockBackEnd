import jieba

text = '我的孩子是年的'

word_list = jieba.cut(text)

for result in word_list:
    print(result)