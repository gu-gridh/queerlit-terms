# Queerlit thesaurus (QLIT) tools

This code is written primarily to fulfill the needs of the [Queerlit](https://queerlit.dh.gu.se/) project, but with the possibility in mind to adapt to other similar projects.

## Use case

- Goal: An RDF/[SKOS](https://www.w3.org/2004/02/skos/) ontology shall be made available online
- Assumption: The source data is a folder of manually edited Turtle (`.ttl`) files adhering to parts of the model
- Requirement: Validate source data (warn on broken references etc)
- Requirement: Complement source data (mirror relations, fix `topConceptOf`, etc)
- Requirement: HTTP server for full data

## Code

This codebase has three parts:

1. [Thesaurus library](#thesaurus-library)
2. [Conversion scripts](#conversion-scripts)
3. [HTTP server](#http-server)

Dependencies can be managed with [Conda](https://docs.conda.io/en/latest/), see [environment.yml](./environment.yml). Most importantly, it is based on [RDFLib](https://rdflib.readthedocs.io/en/stable/) and [Flask](https://flask.palletsprojects.com/en/2.1.x/).

## Thesaurus library

The [thesaurus.py](qlit/thesaurus.py) module defines what we expect to be doing with the thesaurus in code. It extends the RDFLib [Graph](https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.html#rdflib.graph.Graph) class.

The [simple.py](qlit/simple.py) module redefines this slightly, in order to provide plain-JSON responses for use with the [Queerlit GUI](https://github.com/CDH-DevTeam/queerlit-gui).

## Conversion scripts

1. Add to `.env` file: `INDIR="/path/to/ttls"`
2. Run `python3 build.py`

See [build.py](build.py) and [Thesaurus.complete_relations()](qlit/thesaurus.py#L29).

### Persistence for new identifiers

When there are new terms in the source directory, these will be provided with new canonical ids and reported like:

> Creating new identifiers...
> New id gb58ld43 for stockholmareHBTQI
> New id om71eq87 for sånaHBTQI

The new ids are saved to `qlit.nt` but not in the source files, so the next run will generate new ids again. **You must** manually edit the source files and replace temporary ids with the new canonical ones.

## HTTP server

1. Add to `.env` file: `FLASK_ENV=development`
2. Run `flask run`

See [server.py](qlit/server.py).

### HTTP API

| Path                          | Response                                    |
| ----------------------------- | ------------------------------------------- |
| `/`                           | Full RDF data (see _Formats_ below)         |
| `/<name>`                     | RDF data for one term (see _Formats_ below) |
| `/api/`                       | All terms as JSON data                      |
| `/api/term/<name>`            | One term as JSON                            |
| `/api/autocomplete?s=<str>`   | Terms matching a partial label              |
| `/api/roots`                  | All top-level terms                         |
| `/api/children?parent=<name>` | Terms narrower than the term `<name>`       |
| `/api/parents?child=<name>`   | Terms broader than the term `<name>`        |
| `/api/related?other=<name>`   | Terms related to `<name>`                   |

### Formats

The response format for the RDF-oriented routes (i.e. not beginning with `/api/`) can be selected with the `Accept` header or the `format` query param:

```
curl 'https://queerlit.dh.gu.se/qlit/v1/qd17qs25'
curl 'https://queerlit.dh.gu.se/qlit/v1/qd17qs25?format=jsonld'
curl 'https://queerlit.dh.gu.se/qlit/v1/qd17qs25' \
  -H 'Accept: application/rdf+xml'
```

| `format` param  | MIME type             |
| --------------- | --------------------- |
| `ttl` (default) | `text/turtle`         |
| `jsonld`        | `application/ld+json` |
| `xml`           | `application/rdf+xml` |
