"""
Adds missing author information to articles on Wikidata.
"""

import AuthorDatabases as au_db
import NameChecker as ncheck
import DatabaseConnector as sql_db
import pywikibot
from pywikibot import pagegenerators
import re
from datetime import date
from datetime import datetime
import os

term_size = os.get_terminal_size().columns

#connect to wikidata
wd_connect = pywikibot.Site('wikidata', 'wikidata')
wd = wd_connect.data_repository()

#get database pages for referencing
pubmed = pywikibot.ItemPage(wd, 'Q180686')
pmcid = pywikibot.ItemPage(wd, 'Q229883')
dimensions = pywikibot.ItemPage(wd, 'Q95044734')
ads = pywikibot.ItemPage(wd, 'Q752099')

#dictionary where key is compatible database ID and value is database page value for references
db_list = {'P6179': dimensions, 'P698': pubmed, 'P932': pmcid, 'P819': ads}

found_multimatch = sql_db.get_multimatch_articles()
added_authors = []
multiple_matches = {}
unknown_values = []

current_datetime = str(datetime.utcnow())
today = date.today()
pwb_date = pywikibot.WbTime(year=int(today.strftime("%Y")), month=int(today.strftime("%m")), day=int(today.strftime("%d")))

def get_author_items():
    """
    Uses SPARQL query to find Wikidata items with missing author information and a compatible database reference.
    Once found, calls on each Wikidata item to add author information.
    """
    fprint('RUN START: ' + current_datetime)
    with open ('author_finder.rq', 'r') as sparql_file:
        sparql = sparql_file.read()
        sparql = sparql[0:-1]
    generator = pagegenerators.WikidataSPARQLPageGenerator(sparql, site=wd)
    i = 1
    for page in generator:
        fprint((f' {i} ').center(term_size, '='))
        if page.title() not in found_multimatch:
            check_author_info(page)
            i += 1
        else:
            print(page.title() + ' already checked! Moving onto next article.')

def check_author_info(page):
    """
    Checks if existing author items or author name string items exist in Wikidata page.
    If so, checks to see if referenced with a compatible database.
    If so, said database used to obtain missing author information in order to minimise risk of conflicting author information.

    :param page (Pywikibot.ItemPage): Wikidata page with missing author information.

    :return: True if authors successfully added. False otherwise.
    """
    item = page.get()
    try:
        fprint(("Updating author info in: " +  item['labels']['en'] + " (" + page.title() + ")").center(term_size))
    except:
        fprint(("Updating author info in: " + page.title()).center(term_size))

   #see if authors exist
    if 'P50' in item['claims']:
        #checks sources in author property
        db_info = get_source('P50', item)
        if db_info:
            #gets citation from compatible database
            authors = au_db.call_database_api(db_info[1], db_info[0])
            fprint_author_info(authors)
            return add_authors(page, item, authors, db_info[1], db_info[0])

    #see if author name strings exist
    elif 'P2093' in item['claims']:
        #checks sources in author name string property
        db_info = get_source('P2093', item)
        if db_info:
            #gets citation from compatible database
            authors = au_db.call_database_api(db_info[1], db_info[0])
            fprint_author_info(authors)
            return add_authors(page, item, authors, db_info[1], db_info[0])

    #if no authors or author name strings exist
    db_info = find_database(item)
    if db_info:
        authors = au_db.call_database_api(db_info[1], db_info[0])
        #if article has authors
        if len(authors[0]) > 0:
            fprint_author_info(authors)
            return add_authors(page, item, authors, db_info[1], db_info[0])
        else:
            fprint(('No authors found in article.').center(term_size))

def get_source(p_id, item):
    """
    Checks if existing author or author name string item is referenced with a compatible database.

    :param p_id (string): P50 or P2093, representing an existing or author name string item, respectively.
    :param item (dictionary): Wikidata dictionary which contains reference information.

    :return: (s, art_id) (tuple): where s is a compatible database and art_id is the article's ID in said database.
    """
    sources = item['claims'][p_id][0].getSources()

    #if author/name string property has sources...
    if len(sources) > 0:
        #checks if source is compatible database
        for s in sources[0]:
            if s in db_list or s in db_list.items():
            #if it does, use this database to add missing information
                art_id = item['claims'][s][0].getTarget()
                fprint(('Using database ' + s + ' with article ID ' + art_id).center(term_size))
                return (s, art_id)


def find_database(item):
    """
    Finds compatible database in Wikidata item page.

    :param item (dictionary): Wikidata dictionary which contains property information.

    :return: (s, art_id) (tuple): where s is a compatible database and art_id is the article's ID in said database.
    """
    for db in db_list:
        if db in item['claims']:
            #get author citation from compatible database
            art_id = item['claims'][db][0].getTarget()
            fprint(('Using database ' + db +  ' with article ID ' + art_id).center(term_size))
            return (db, art_id)

    #since all articles in SPARQL query should have a compatible database, return false if something has gone wrong.
    fprint('An error has occurred - SPARQL query returned unwanted results.')
    return False

def add_authors(page, item, authors, art_id, db):
    """
    Adds missing author information to Wikidata item page.

    :param page (Pywikibot.ItemPage): Wikidata item where information will be added.
    :param item (Dictionary): Wikidata dictionary with claim information.
    :param authors (tuple): tuple composed of two lists composed of author given names and last names
    :param art_id (string): article ID
    :param db (string): database being used

    :return: True if authors added successfully.
    """

    updated_authors = []
    authors_to_delete = []

    for i, given_name in enumerate(authors[0]):

        #not yet found in author/author name string pages
        author = []
        family_name = authors[1][i]
        full_name = given_name + ' ' + family_name

        fprint('\nAdding author: ' + full_name)
        if 'P50' in item['claims']:
            fprint('== Trying to find author in existing author items...')
            author = find_author(updated_authors, page, item, 'P50', given_name, family_name, full_name, author, i)
        if 'P2093' in item['claims'] and not author == 2:
             fprint('== Trying to find author in existing author name string items...')
             author = find_author(updated_authors, page, item, 'P2093', given_name, family_name, full_name, author, i)

        if author == 2:
            continue

        elif len(author) >= 1:
            author_info = [full_name, given_name, family_name, i, db, art_id]
            if len(author) > 1:
                try:
                    au = next(au for au in author if au[0].id == 'P50')
                    del_au = next(au[0] for au in author if au[0].id == 'P2093')
                    authors_to_delete.append(del_au)
                    updated_authors.append(del_au.getTarget())
                except:
                    au = next(au for au in author if au[1] == 1)
                updated_authors = add_author_information(updated_authors, au[0], author_info)
            else:
                updated_authors = add_author_information(updated_authors, author[0][0], author_info)

        else:
            fprint('== Author not found on page! Adding author name string property.')
            added_authors.append((full_name, page.title()))
            au = pywikibot.Claim(wd, u'P2093')
            au.setTarget(full_name)
            updated_authors.append(full_name)
            page.addClaim(au, summary=u'Adding author name string')
            fprint('== Adding qualifiers to author name string item...')
            add_author_qualifiers(au, full_name, given_name, family_name, i)
            add_reference(au, db, art_id, pwb_date)

    delete_claim(page, unknown_values)
    delete_claim(page, authors_to_delete)
    return True

def find_author(updated_authors, page, item, claim, given_name, family_name, full_name, author, i):
    """
    Iterates through authors/author name strings on Wikidata and finds a match with a provided author
    :param updated_authors (list): list of authors whose information has already been updated
    :param page (Pywikibot.Page): Pywikibot page to get title from if multiple match found
    :param item (Pywikibot.Item): ItemPage to add author information to
    :param given_name (str): Author's given name
    :param family_name (str): Author's family name
    :param full_name (str): Author's full name
    :param i (int): Current author's series ordinal position, used to check for series ordinal matches if other match types aren't found
    :return: The updated author match list, 2 if multiple incompatible matches found.
    """
    for au in item['claims'][claim]:
        au_t = au.getTarget()
        if au_t == None:
            print('==*       Unknown value found in page! Will delete after adding author information...')
            if (au, page) not in unknown_values:
                unknown_values.append((page, au))
        elif au_t not in updated_authors:
            author_check = ncheck.check_name(au, given_name, family_name, full_name)
            if not author_check and u'P1545' in au.qualifiers and int(au.qualifiers[u'P1545'][0].getTarget()) == i+1:
                author_check = ncheck.lenient_check(au, given_name, family_name, full_name)
            if author_check:
                author.append((au, author_check))
                if len(author) > 1 and check_multiple_matches(author):
                    multiple_matches.setdefault(page.title(), {}).update({full_name : author})
                    return 2
    return author

def add_author_information(updated_authors, author, author_info):
    """
    Gets needed author information to append to updated authors list, and adds qualifiers and references to Wikidata.
    :param updated_authors (list): List with authors with information already added to wikidata
    :param author (Pywikibot.Claim): Author claim to add information to
    :param author_info (list) list containing author given name, last name, full name, and database info to add to Wikidata
    """
    try:
        fprint('== Correct match found!: ' + author.getTarget().get()['labels']['en'])
        updated_authors.append(author.getTarget())
    except:
        fprint('== Correct match found!: ' + author.getTarget())
        updated_authors.append(author.getTarget())
    add_author_qualifiers(author, author_info[0], author_info[1], author_info[2], author_info[3])
    add_reference(author, author_info[4], author_info[5], pwb_date)
    return updated_authors

def check_multiple_matches(author):
    """
    Checks for multiple matches for a given author.
    :param author (list): list with multiple author finds that may or may not be incompatible.
    :return True if multiple exact or heuristic matches, False otherwise
    """
    multiple_match = len(author) > 1 and any(m_type[1] == author[0][1] for m_type in author)
    if multiple_match:
        if (u'P1545' in author[0][0].qualifiers and u'P1545' in author[1][0].qualifiers
            and author[0][0].qualifiers[u'P1545'] == author[1][0].qualifiers[u'P1545']
           and not author[0][0].id == author[1][0].id):
            print('==*   Identical author and author name string match! Will delete author name string.')
            return False
        else:
            fprint('== Multiple matches found on page! Skipping this author.')
            return True
    return False


def add_author_qualifiers(author, full_name, given_name, family_name, i):
    """
    Iterates through necessary author qualifiers and adds them.

    :param author (Pywikibot.Claim): author claim that qualifiers will be added to
    :param given_name (string): author given name
    :param family_name (string): author family name
    :param i (int): index count eventually transformed into author series ordinal
    """
    fprint('== Adding qualifiers...')
    if isinstance(author.getTarget(), pywikibot.ItemPage):
        add_qualifier(author, full_name, u'P1932')
    au_properties = {u'P9687':given_name, u'P9688':family_name, u'P1545':str(i+1)}
    for p in au_properties:
        add_qualifier(author, au_properties[p], p)

def add_qualifier(claim, value, pid):
    """
    Adds qualifier to Wikidata item property.

    :param claim (Pywikibot.Claim): claim to add qualifier to
    :param value (string): value of qualifier
    :param pid (string): Property ID of qualifier being added
    """

    if pid not in claim.qualifiers:
        qualifier = pywikibot.Claim(wd, pid)
        qualifier.setTarget(value)
        claim.addQualifier(qualifier)
        fprint('==\tAdded ' + pid + ': ' + value)
    else:
        fprint('==\t' + pid + ' already in author item!')

def add_reference(author, db, art_id, pwb_date):
    """
    Adds reference to author item.

    :param author (Pywikibot.Claim): author claim to add reference to
    :param db (string): database where reference found
    :param art_id (string): item article ID.
    """
    fprint('== Adding references...')
    try:
        sources = set()
        for source in author.getSources():
            sources.update(source.keys())
    except:
        sources = []
    if db_list[db] not in sources and db not in sources:
        stated_in = pywikibot.Claim(wd, u'P248')
        stated_in.setTarget(db_list[db])
        db_ref = pywikibot.Claim(wd, u''+ db)
        db_ref.setTarget(art_id)
        retrieved = pywikibot.Claim(wd, u'P813', is_reference=True)

        retrieved.setTarget(pwb_date)
        try:
            author.addSources([stated_in, db_ref, retrieved])
            fprint('==\tSuccessfully added reference to author item.')
        except:
            fprint('==\tAuthor information already has reference!')
    else:
        fprint('==\tAuthor information already referenced with corresponding database!')

def fprint_author_info(authors):
    """
    Formatting function which nicely fprints author names.

    :param authors (tuple): tuple with two lists including author family and given names.
    """
    fprint(('Author given names: ' +  str(authors[0])).center(term_size))
    fprint(('Author family names: ' + str(authors[1])).center(term_size))
    fprint('=' * term_size)

def print_tricky_authors():
    tricky_print('RUN TIME: ' + current_datetime)
    tricky_print('Added Authors: ')
    for author in added_authors:
        tricky_print('Added author ' + author[0] + ' in article: ' + author[1])
    tricky_print('Multiple Matches: ')
    for multimatch in multiple_matches:
        tricky_print('Multiple match in article ' + multimatch + ': ')
        for au in multiple_matches[multimatch]:
            tricky_print(au)

def fprint(string):
    print(string)
    with open('authorbot_run.txt', 'a') as f:
        f.write('{}\n'.format(string))

def tricky_print(string):
    print(string)
    with open('tricky_authors.txt', 'a') as f:
        f.write('{}\n'.format(string))

def delete_claim(page, del_authors):
    for author in del_authors:
        fprint('== Deleting author: ' + author.getTarget() + ' in page ' + page.title())
        page.removeClaims(author, summary=u'Removed unnecessary author')

test = pywikibot.ItemPage(wd, 'Q21045384')
check_author_info(test)
get_author_items()
print_tricky_authors()
sql_db.add_multiple_match(multiple_matches)
