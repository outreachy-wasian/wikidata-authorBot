"""
Gets author given and family names by calling a database API.
"""

import urllib.request
import requests
import re

#mbib format works for pubmed and pcmid articles
#ris format works for ads, dimensionis, and researchgate articles
#TODO: get CJFD articles working.
citation_regex = {'mbib' : r'FAU - (.*), (.*)\r','RIS' : r'AU  - (.*), ([^\r\n]*)', 'EndNote' : r'%A (.{1}?)(.{2}?)[\n<br>]'}

#gets tokens for APIs
with open('api_keys.txt') as file:
    _api_keys = file.read().splitlines()


def generate_database_info(art_id, database):
    """
    Generate correct API, header, and params for a given article in a database
    :param art_id (string): article ID in database
    :param database (string): database, found as dict key

    :return correctly formed database list
    """
    #Dictionary is as follows: Database: [URL, Headers, Params, Citation Format]
    database_dict = {
        #CJFD exportCitation API
        'P6769' : ['https://kns.cnki.net/kns8/manage/APIGetExport',
                   {'Referer' : 'https://kns.cnki.net/kcms/detail/detail.aspx?dbcode=CJFD&filename=' + art_id},
                   {'filename':'CJFD2005!' + art_id + '!1!0', 'displaymode':'EndNote'},
                    'EndNote'],
        'P932' : ['https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/pmc/?format=medline&id=' + art_id + '&api_key=' + _api_keys[0], 'mbib'],
        #Pubmed Literature Citation Exporter: https://api.ncbi.nlm.nih.gov/lit/ctxp
        'P698' : ['https://api.ncbi.nlm.nih.gov/lit/ctxp/v1/pubmed/?format=medline&id=+' + art_id + '&api_key=' + _api_keys[0], 'mbib'],
        #Dimensions Publication Export Citation API
        'P6179' : ['https://app.dimensions.ai/details/sources/publication/export/pub.' + art_id + '/citation/ris', 'RIS'],
        #ADS Bibcode Export API
        'P819' : ['https://api.adsabs.harvard.edu/v1/export/ris/' + art_id,
                  {'Authorization':'Bearer:' + _api_keys[1]}, 'RIS']
    }
    return database_dict[database]


def call_database_api(art_id, database):
    """
    Call correct database API to generate accurate reference.
    :param art_id (string): article ID
    :param database (string): database
    :return author tuple
    """
    user_agent = 'AuthorBot_Wikidata'
    headers = {'User-Agent':user_agent}
    cit_info = generate_database_info(art_id, database)
    #if headers needed
    if len(cit_info) >= 3:
        headers = headers | cit_info[1]
    url = cit_info[0]
    #if not CJFD
    if not database == 'P6769':
        html = requests.get(url, headers=headers)
        html.encoding = 'utf-8'
        citation = str(html.text)
    else:
        params = cit_info[2]
        html = requests.post(url, json=params, headers=headers)
        html.encoding = 'utf-8'
        citation = str(html.json()['data'][0]['value'][0])
    return get_authors(cit_info[-1], citation)

def get_authors(cit_format, citation):
    """
    Generate author tuple from citation
    :param cit_format (str): what format the citation will be in (mbib, RIS, or Endnote)
    :param citation (str): the complete citation to extract author names from

    :return authors (tuple): tuple consisting of two lists of author family names and given names.
    """
    author_family_names = []
    author_given_names = []
    authors_re = re.compile(citation_regex[cit_format])
    for author in authors_re.finditer(citation):
        author_given_names.append(author.group(1))
        author_family_names.append(author.group(2))
    authors = (author_family_names, author_given_names)
    return authors
