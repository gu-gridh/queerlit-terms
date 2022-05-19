"""
Saves copies of all source files with randomized identifiers.
"""

from datetime import date, datetime
from os import makedirs
from dotenv import load_dotenv
from isodate import date_isoformat
from rdflib import DCTERMS, Literal, URIRef
from strgen import StringGenerator
from qlit.simple import name_to_ref, ref_to_name
from qlit.thesaurus import Thesaurus

load_dotenv()

thesaurus = Thesaurus().parse('qlit.nt')
old_refs = thesaurus.refs()

id_generator = StringGenerator(r'[a-z]{2}[0-9]{2}[a-z]{2}[0-9]{2}')
new_ids = id_generator.render_set(len(old_refs))

old_ids = [ref_to_name(old_ref) for old_ref in old_refs]
new_refs = [name_to_ref(new_id) for new_id in new_ids]
items = list(zip(old_refs, new_refs, old_ids, new_ids))

if __name__ == '__main__':
    for (old_ref, new_ref, old_id, new_id) in items:
        print(old_id, '\t', new_id)
        # Update outgoing statements
        for p, o in thesaurus.predicate_objects(old_ref):
            thesaurus.remove((old_ref, p, o))
            thesaurus.add((new_ref, p, o))
        # Update incoming relations
        for s, p in thesaurus.subject_predicates(old_ref):
            thesaurus.remove((s, p, old_ref))
            thesaurus.add((s, p, new_ref))
        # Update identifier literal
        thesaurus.set((new_ref, DCTERMS.identifier, Literal(new_id)))

    outdir = f'out/randomids-{datetime.now().isoformat(timespec="seconds")}'
    makedirs(outdir)

    for (old_ref, new_ref, old_id, new_id) in items:
        termset = thesaurus.terms_if(lambda term: term == new_ref)
        termset.serialize(f'{outdir}/{old_id}.ttl', 'ttl')