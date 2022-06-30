import pywikibot
from pywikibot import pagegenerators
import re
import AuthorDatabases as au_db

#connects to wikidata
wd_connect = pywikibot.Site('wikidata', 'wikidata')
wd = wd_connect.data_repository()
#database list in priority order
#order: cjfd, pubmed, dimensionis, ads
db_list = ['P698', 'P6179', 'P819']
#SPARQL query that finds items with missing author information + suitable database citations
def get_author_items():
    with open ('author_finder.rq', 'r') as sparql_file:
        sparql = sparql_file.read()
        sparql = sparql[0:len(sparql) - 1]
    generator = pagegenerators.WikidataSPARQLPageGenerator(sparql, site=wd)
    for page in generator:
        check_author_info(page)

#checks if authors exist in page and if they have sources
def check_author_info(page):
    item = page.get()
    print("\n----------------------------------------------------------------------------")
    print("Updating author info in: " + item['labels']['en'] + ' (' + page.title() + ')' )
    #see if authors exist
    if 'P50' in item['claims']:
        #checks sources in author property
        get_sources('P50', item)
    #see if author name strings exist
    elif 'P2093' in item['claims']:
        #checks sources in author name string property
        get_sources('P2093', item)
    else:
        find_database(item)

def get_sources(p_id, item):
    sources = item['claims'][p_id][0].getSources()
    #if author/name string property has sources...
    if len(sources) > 0:
        #checks if source in preexisting author item exists in database list
        for s in sources[0]:
            if s in db_list:
                #if it does, add it using said database for convenience.
                #TODO: if names appear to be chinese prioritise CJFD no matter what?
                db_id = item['claims'][s][0].getTarget()
                print(db_id)
                add_authors(s, db_id)
                return True
        find_database(item)
    #if author/name string property has no sources...
    else:
        find_database(item)

def find_database(item):
    for db in db_list:
        #look for compatible database in identifiers
        if db in item['claims']:
            #add authors
            db_id = item['claims'][db][0].getTarget()
            print("\n" + db + ": " + db_id)
            add_authors(db, db_id)
            return True
    print('An error has occurred - SPARQL query returned unwanted results.')
    return False


def add_authors(data, db_id):
    #get database API that returns a list of authors
    citation = au_db.call_database_api(db_id, data)

get_author_items()
