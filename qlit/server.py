from flask import Flask, Response, jsonify, make_response, request

from qlit.simple import SimpleThesaurus, name_to_ref
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

# "Rdf" routes are in RDF space.


@app.route('/')
def rdf_all():
    return termset_response(THESAURUS)


@app.route('/<name>')
def rdf_one(name):
    # TODO Handle 404
    ref = name_to_ref(name)
    return termset_response(THESAURUS.get(ref))

# "Api" routes are in simple non-RDF space.


@app.route("/api/")
def api_all():
    return jsonify(THESAURUS_SIMPLE.get_all())


@app.route("/api/<name>")
def api_one(name):
    # TODO Handle 404
    return jsonify(THESAURUS_SIMPLE.get(name))


@app.route("/api/roots")
def api_roots():
    return jsonify(THESAURUS_SIMPLE.get_roots())


@app.route("/api/children")
def api_children():
    # TODO Handle missing/bad arg
    # TODO Distinguish 404 from leaf
    parent = request.args.get('parent')
    return jsonify(THESAURUS_SIMPLE.get_children(parent))


@app.route("/api/parents")
def api_parents():
    # TODO Handle missing/bad arg
    # TODO Distinguish 404 from root
    child = request.args.get('child')
    return jsonify(THESAURUS_SIMPLE.get_parents(child))
