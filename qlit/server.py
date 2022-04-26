from flask import Flask, Response, jsonify, make_response, request

from qlit.simple import SimpleThesaurus
from .thesaurus import Termset, Thesaurus

app = Flask(__name__)

THESAURUS = Thesaurus().parse('qlit.ttl')
THESAURUS_SIMPLE = SimpleThesaurus() + THESAURUS


def termset_response(termset: Termset) -> Response:
    """Use preferred MIME type for serialization and response."""
    # Default to Turtle
    mimetype = request.accept_mimetypes.best.replace('*/*', 'text/turtle')
    # TODO Handle unsupported mimetype.
    # Allowed are at least: application/ld+json, text/turtle
    data = termset.serialize(format=mimetype)
    return make_response(data, 200, {'Content-Type': mimetype})


@app.route('/')
def home():
    return termset_response(THESAURUS)


@app.route("/api/roots")
def roots():
    return jsonify(THESAURUS_SIMPLE.get_roots())


@app.route("/api/children")
def children():
    # TODO Distinguish 404 from leaf
    parent = request.args.get('parent')
    return jsonify(THESAURUS_SIMPLE.get_children(parent))


@app.route("/api/parents")
def parents():
    # TODO Distinguish 404 from root
    child = request.args.get('child')
    return jsonify(THESAURUS_SIMPLE.get_parents(child))
