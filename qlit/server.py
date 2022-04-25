import json
from flask import Flask, Response, make_response, request
from .thesaurus import Termset, Thesaurus

app = Flask(__name__)


THESAURUS = Thesaurus().parse('qlit.ttl')


def termset_response(termset: Termset) -> Response:
    mimetype = request.accept_mimetypes.best
    if (mimetype == '*/*'):
        mimetype = 'text/turtle'
    data = termset.serialize(format=mimetype)
    return data, 200, {
        'Content-Type': mimetype
    }


@app.route("/roots")
def roots():
    return termset_response(THESAURUS.get_roots())
