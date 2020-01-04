from src.service.StockService import StockService
from src.service.HtmlService import get_response

url = 'https://api-secure.wsj.net/api/michelangelo/timeseries/history'

_datetime = '1577664000000'

params = {
'json': '{"Step":"PT1M","TimeFrame":"D1","StartDate":1577664000000,"EndDate":1577664000000,"EntitlementToken":"cecc4267a0194af89ca343805a3e57af","IncludeMockTick":true,"FilterNullSlots":false,"FilterClosedPoints":true,"IncludeClosedSlots":false,"IncludeOfficialClose":true,"InjectOpen":false,"ShowPreMarket":false,"ShowAfterHours":false,"UseExtendedTimeFrame":true,"WantPriorClose":false,"IncludeCurrentQuotes":false,"ResetTodaysAfterHoursPercentChange":false,"Series":[{"Key":"INDEX/CN/XSHG/SHCOMP","Dialect":"Charting","Kind":"Ticker","SeriesId":"s1","DataTypes":["Last"],"Indicators":[{"Parameters":[{"Name":"Period","Value":"50"}],"Kind":"SimpleMovingAverage","SeriesId":"i2"},{"Parameters":[],"Kind":"Volume","SeriesId":"i3"},{"Parameters":[{"Name":"EMA1","Value":12},{"Name":"EMA2","Value":26},{"Name":"SignalLine","Value":9}],"Kind":"MovingAverageConvergenceDivergence","SeriesId":"i4"},{"Parameters":[{"Name":"ShowOpen"},{"Name":"ShowHigh"},{"Name":"ShowLow"},{"Name":"ShowPriorClose","Value":true},{"Name":"Show52WeekHigh"},{"Name":"Show52WeekLow"}],"Kind":"OpenHighLowLines","SeriesId":"i5"}]}]}',
'ckey': 'cecc4267a0'
}

headers = {
    'Dylan2010.EntitlementToken': 'cecc4267a0194af89ca343805a3e57af'
}

result = get_response(url, params=params, headers=headers,use_proxy=True)

print(result)
