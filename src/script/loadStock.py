from src.utils.stock import getStockList
from src.utils.db import MySQL

list = getStockList()

mysql = MySQL()

for item in list:
    result = mysql.execute('insert into `stock`(`name`, `code`) values (%s, %s)', item)
    print(result)