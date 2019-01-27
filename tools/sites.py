#!/usr/bin/python3

# NOTE: run this very infrequently and update the "sites" variable in data.py

# import json
# import requests
# print([x['api_site_parameter'] for x in json.loads(requests.get('https://api.stackexchange.com/2.2/sites?pagesize=9999&filter=!6Oe78nmjjzwCi').text)['items'] if x['site_type'] == 'main_site'])

import requests
from bs4 import BeautifulSoup
b = BeautifulSoup(requests.get('https://stackexchange.com/sites').text)
print([
    [x['href'][8:], int(x.find(class_='gv-stats').find('span')['title'].split()[0].replace(',', ''))]
    for x in b.find(class_='grid-view-container').find_all('a', recursive=False)
    ])
