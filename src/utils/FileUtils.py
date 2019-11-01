'''
    文件操作类
'''

import os
from src.static import static_dir_path


# 生成文件
def generate_file(file_name, content, file_dir):
    file = open(file_dir + os.sep + file_name, 'w')
    file.write(content)
    file.flush()
    file.close()


# 生成静态目录下的文件
def generate_static_dir_file(file_name, content):
    return generate_file(file_name, content, static_dir_path)
