"""
Checks whether two given names are a match.
"""

import re
import pywikibot
from unidecode import unidecode
from difflib import SequenceMatcher

#connect to wikidata
def check_name(author, given_name, family_name, full_name):
    """
    Checks if an author or author name string item are a match.
    :param author_item (Pywikibot.ItemPage or string): author to check against
    :param given_name (string): author given name
    :param family_name (string): author family name
    :param full_name (string): author full name

    :return: the author item if match found, False otherwise
    """
    try:
        author_name = author.getTarget().get()['labels']['en']
    except:
        author_name = author.getTarget()
    try:
        author_aliases = author.getTarget().get()['aliases']['en']
    except:
        author_aliases = []

    #if author label and citation name are exact, accept
    if author_name == full_name:
        print('==\tPerfect match!: ' + author_name)
        return 1

    for alias in author_aliases:
        if alias == full_name:
            print('==\tAlias match!: ' + alias)
            return 1

    if u'P1932' in author.qualifiers:
        stated_as = author.qualifiers[u'P1932'][0].getTarget()
        stated_as_simple = re.sub('\W+', '', stated_as)
        if stated_as == full_name or stated_as_simple == full_name:
            print('==\tStated as match!: ' + author_name)
            return 1

    #remove non-alphabet characters to simplify finding matches
    s_given_name = re.split('\W+', given_name)
    s_family_name = re.split('\W+', family_name)
    s_author_name = re.split('\W+', author_name)
    #if first given names are the same
    if (    s_given_name[0] == s_author_name[0]
        #or, if first given name is an acronym, initials are the same
        or  (   len(s_given_name[0]) == 1
             and s_given_name[0] == s_author_name[0][:1])
        #or, the same if special characters removed from names
        or  (   s_given_name[0] == s_author_name[0] + s_author_name[1]  )
        #or, the same if transliterated
        or  (   unidecode(s_given_name[0]) == unidecode(s_author_name[0]))
       ):
        #and last names are the same 
        #(checking for possible eliminations in double-barrelled names)
        uni_author_name = unidecode(author_name)
        uni_s_family_name = []
        for n in s_family_name:
            uni_s_family_name.append(unidecode(n))
        if (any(n in author_name for n in s_family_name)
            or (any(n in uni_author_name for n in uni_s_family_name))
           ):
            #and, if relevant, middle initials are the same
            #if there is a middle name
            if len(s_given_name) > 1:
                au_m_initial = get_middle_initial(s_author_name)
                #check case where middle initials are different
                if (au_m_initial and not au_m_initial == s_given_name[1][:1]):
                    print('==\tNo match! Incorrect middle initial: ' + author_name)
                    return 0
            print('==\tHeuristic match!: ' + author_name)
            return 2
        print('==\tNo match! Incorrect surnames: ' + author_name)
        return 0
    print('==\tNo match! Incorrect given names: ' + author_name)
    return 0

def lenient_check(author, given_name, family_name, full_name):
    try:
        author_name = author.getTarget().get()['labels']['en']
    except:
        author_name = author.getTarget()

    name_similarity_ordered = SequenceMatcher(None, author_name, full_name)
    name_similarity_backwards = SequenceMatcher(None, author_name, family_name + given_name)
    if name_similarity_ordered.ratio() >= 0.8 or name_similarity_backwards.ratio() >= 0.8:
        print('==\t Lenient match found via series ordinal matching: ' + author_name)
        return 1

def get_middle_initial(author_name):
    """
    Checks if an author name has a middle initial
    :param author_name (list): author name split
    :return: the initial if exists, false otherwise
    """
    if len(author_name) > 2 and len(author_name[1]) == 1:
            return author_name[1]
    return False


