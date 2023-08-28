from flask import Flask, Response, jsonify, make_response, request
from flask_cors import CORS
from qlit.thesaurus import TermNotFoundError, Termset, Thesaurus
from qlit.simple import SimpleThesaurus, name_to_ref

app = Flask(__name__)
CORS(app)

THESAURUS = Thesaurus().parse('qlit.nt')
print(f'Loaded thesaurus with {len(THESAURUS.refs())} terms')

THESAURUS_SIMPLE = SimpleThesaurus(THESAURUS)

FORMATS = {
    'ttl': 'text/turtle',
    'jsonld': 'application/ld+json',
    'xml': 'application/rdf+xml',
}


def find_mimetype() -> str:
    # First prio: `format` param
    format_param = request.args.get('format')
    if format_param and FORMATS.get(format_param):
        return FORMATS.get(format_param)

    # Next prio: `Accept` header
    header_mimetype = request.accept_mimetypes.best
    if header_mimetype and header_mimetype in FORMATS.values():
        return header_mimetype

    # Fall back to Turtle
    return 'text/turtle'


def termset_response(termset: Termset) -> Response:
    """Use preferred MIME type for serialization and response."""
    mimetype = find_mimetype()

    data = termset.serialize(format=mimetype)

    # Specify encoding.
    if mimetype.startswith('text/'):
        mimetype += '; charset=utf-8'

    return make_response(data, 200, {'Content-Type': mimetype})


# "Rdf" routes are in RDF space.


@app.route('/')
def rdf_all():
    return termset_response(THESAURUS)


@app.route('/<name>')
def rdf_one(name):
    ref = name_to_ref(name)
    return termset_response(THESAURUS.get(ref))

# "Api" routes are in simple non-RDF space.


@app.route("/api/")
def api_all():
    return jsonify(THESAURUS_SIMPLE.get_all())


@app.route("/api/term/<name>")
def api_one(name):
    return jsonify(THESAURUS_SIMPLE.get(name))


@app.route("/api/labels")
def api_labels():
    return jsonify(THESAURUS_SIMPLE.get_labels())


@app.route("/api/autocomplete")
def api_autocomplete():
    # TODO Handle missing/bad arg
    s = request.args.get('s')
    return jsonify(THESAURUS_SIMPLE.autocomplete(s))


@app.route("/api/collections")
def api_collections():
    return jsonify(THESAURUS_SIMPLE.get_collections())


@app.route("/api/collections/<name>")
def api_collection(name):
    tree = bool(request.args.get('tree'))
    return jsonify(THESAURUS_SIMPLE.get_collection(name, tree))


@app.route("/api/roots")
def api_roots():
    return jsonify(THESAURUS_SIMPLE.get_roots())


@app.route("/api/children")
def api_children():
    # TODO Handle missing/bad arg
    parent = request.args.get('parent')
    return jsonify(THESAURUS_SIMPLE.get_children(parent))


@app.route("/api/parents")
def api_parents():
    # TODO Handle missing/bad arg
    child = request.args.get('child')
    return jsonify(THESAURUS_SIMPLE.get_parents(child))

@app.route("/api/related")
def api_related():
    # TODO Handle missing/bad arg
    other = request.args.get('other')
    return jsonify(THESAURUS_SIMPLE.get_related(other))


@app.errorhandler(TermNotFoundError)
def handle_term_not_found(e):
    return make_response(jsonify({
        'status': 'error',
        'message': str(e),
    }), 404)
