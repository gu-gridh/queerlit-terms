from flask import Flask, Response, jsonify, make_response, request
from qlit.thesaurus import Termset, Thesaurus
from qlit.simple import SimpleThesaurus, name_to_ref
from rdflib.plugin import PluginException

app = Flask(__name__)

THESAURUS = Thesaurus().parse('qlit.nt')
THESAURUS_SIMPLE = SimpleThesaurus() + THESAURUS

print(f'Loaded thesaurus with {len(THESAURUS.refs())} terms')


def termset_response(termset: Termset) -> Response:
    """Use preferred MIME type for serialization and response."""
    # Default to Turtle
    DEFAULT_MIMETYPE = 'text/turtle'
    mimetype = request.accept_mimetypes.best.replace('*/*', DEFAULT_MIMETYPE)
    # Allowed are at least: application/ld+json, text/turtle
    try:
        data = termset.serialize(format=mimetype)
    except PluginException:
        mimetype = DEFAULT_MIMETYPE
        data = termset.serialize(format=mimetype)

    # For Turtle, specify encoding. For other formats, the encoding is
    if mimetype.startswith('text/'):
        mimetype += '; charset=utf-8'

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
