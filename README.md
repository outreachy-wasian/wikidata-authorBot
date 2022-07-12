This script is run by [PangolinBot](https://www.wikidata.org/wiki/User:PangolinBot/) and was created by [PangolinMexico](https://www.wikidata.org/wiki/User:PangolinBot/).

This was created for the ['What's in a Name?:' Automatically detecting first and last author names on Wikidata.'](https://phabricator.wikimedia.org/T300207) project as part of [Outreachy Round 24.](outreachy.org/)

AuthorBot adds missing author information to scientific article pages on Wikidata. Authorbot is currently compatible with the following academic databases:
- Pubmed (Pubmed ID = [P698](https://www.wikidata.org/wiki/Property:P698), Pubmed = [Q180686](https://www.wikidata.org/wiki/Q180686))
- Dimensions Publications (Dimensions ID = [P6179](https://www.wikidata.org/wiki/Property:P6179), Dimensions Publications = [Q95044734](https://www.wikidata.org/wiki/Q95044734))
- Astrophysics Database Service (ADS ID = [P819](https://www.wikidata.org/wiki/Property:P819), ADS = [Q752099](https://www.wikidata.org/wiki/Q752099))

In the future, I aim to make AuthorBot compatible with the following academic databases:
- CJFD
- PCMID
- arXiV

If you want compatibility with a specific academic database, feel free to request it! Write a message on the PangolinBot or PangolinMexico User page.

# Features:
- Gets articles on Wikidata that are missing author information and are cited in a compatible database. This includes:
1. Scientific papers (items where P31 = Q13442814) with no P50 or no P2093 statements
2. Articles with P50 and/or P2093 statements that are missing:
  - no object stated as (P1932) qualifier (For P50 items only)
  - no author first name (P9687) qualifier
  - no author last name (P9688) qualifier
- Extracts citations using database APIs for the aforementioned compatible databases
- Adds the aforementioned properties to scientific paper items on Wikidata. 
- Is able to both add author item statements and detect existing author information and add missing info to it, as well as detecting slight difference by checking aliases and acronyms.

# Things to improve/Future features:
- One-by-one API extraction: Unable to get a 'batch' set of author citations, which would reduce author calls considerably
- Author name string default: Currently, if an author is not already on the Wikidata page, they are added an as author name string property as there is no clear way to definitively find a P50 page that corresponds to a citation's author through just their name. In the future, could be possible to extract ORCID IDs from the article.

#Note:
- If for some reason you want to try running this script yourself, you will need your own API keys for Pubmed, ADS, and Dimensions. Mine are kept private for hopefully obvious reasons.
