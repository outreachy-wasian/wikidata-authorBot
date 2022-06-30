import urllib.request
import requests
import re
#mbib format works for pubmed and pcmid articles
#ris format works for ads, dimensionis, and researchgate articles
citation_regex = {'mbib' : r'FAU - (.*), (.*)\r','RIS' : r'AU  - (.*), ([^\r\n]*)', 'EndNote' : r'%A (.{1}?)(.{2}?)[\n<br>]'}
with open('api_keys.txt') as file:
    api_keys = file.read().splitlines()

#DATABASE: [URL, HEADERS, PARAMS]
#TODO: Discuss organisation with Mike, unsure if this is the best way to organise this data
def generate_database_info(art_id, database):
    database_dict = {
        #CJFD exportCitation API
        'P6769' : ['https://kns.cnki.net/kns8/manage/APIGetExport',
                   {'Referer' : 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=' + art_id},
                   {'filename':'CJFD2005!' + art_id + '!1!0', 'displaymode':'EndNote'},
                    'EndNote'],
        #Pubmed Literature Citation Exporter: https://api.ncbi.nlm.nih.gov/lit/ctxp
        'P698' : ['https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/pubmed/?format=medline&id=+' + art_id + '&api_key=' + api_keys[0], 'mbib'],
        #Dimensions Publication Export Citation API
        'P6179' : ['https://app.dimensions.ai/details/sources/publication/export/pub.' + art_id + '/citation/ris', 'RIS'],
        #ADS Bibcode Export API
        'P819' : ['https://api.adsabs.harvard.edu/v1/export/ris/' + art_id,
                  {'Authorization':'Bearer:' + api_keys[1]}, 'RIS']
    }
    return database_dict[database]


#works for all implemented databases except CJFD
#this is kind of suspicious right now
def call_database_api(art_id, db):
    user_agent = 'AuthorBot_Wikidata'
    headers = {'User-Agent':user_agent}
    database = generate_database_info(art_id, db)
    if len(database) >= 3:
        headers = headers | database[1]
    url = database[0]
    if not db == 'P6769':
        html = requests.get(url, headers=headers)
        html.encoding = 'utf-8'
        citation = str(html.text)
    else:
        params = database[2]
        html = requests.post(url, json=params, headers=headers)
        html.encoding = 'utf-8'
        citation = str(html.json()['data'][0]['value'][0])
    return get_authors(database[-1], citation)

def get_authors(cit_format, citation):
    author_family_names = []
    author_given_names = []
    authors_re = re.compile(citation_regex[cit_format])
    for author in authors_re.finditer(citation):
        author_given_names.append(author.group(1))
        author_family_names.append(author.group(2))
    authors = [author_family_names, author_given_names]
    print(authors)
    return authors

call_database_api('2004ApJ...606L.155B', 'P819')
