import requests

url = 'https://kns.cnki.net/kns8/manage/APIGetExport'

def call_database_api(url):
    user_agent = 'AuthorBot_Wikidata'
    params = {'filename':'CJFD7984!kagu196511010!1!0', 'displaymode':'EndNote'}
    headers = {'User-Agent':user_agent, 'Referer':
	'https://oversea.cnki.net/KCMS/detail/detail.aspx?dbcode=CJFD&dbname=CJFD7984&filename=KAGU196511010'}
    html = requests.post(url, json=params, headers=headers)
    return str(html.json()['data'][0]['value'][0])

api = call_database_api(url)
print(api)
