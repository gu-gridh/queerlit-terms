# Queerlit thesaurus (QLIT) tools

This code is written primarily to fulfill the needs of the [Queerlit](https://queerlit.dh.gu.se/) project, but with the possibility in mind to adapt to other similar projects.

## Use case

- Goal: An RDF/[SKOS](https://www.w3.org/2004/02/skos/) ontology shall be made available online
- Assumption: The source data is a folder of manually edited Turtle (`.ttl`) files adhering to parts of the model
- Requirement: Validate source data (warn on broken references etc)
- Requirement: Complement source data (mirror relations, fix `topConceptOf`, etc)
- Requirement: HTTP server for full data

## Development

This codebase has three parts:

1. [Thesaurus library](#thesaurus-library)
2. [Conversion scripts](#conversion-scripts)
3. [HTTP server](#http-server)

Dependencies can be managed with [Conda](https://docs.conda.io/en/latest/), see [environment.yml](./environment.yml). Most importantly, it is based on [RDFLib](https://rdflib.readthedocs.io/en/stable/) and [Flask](https://flask.palletsprojects.com/en/2.1.x/).

### Branch model

Commit changes to the `dev` branch and make sure to keep [CHANGELOG.md](CHANGELOG.md) updated. Data updates with `build.py` do not need to be changelogged.

To release:

1. Update [CHANGELOG.md](CHANGELOG.md):
   1. Determine new version number
   2. Add a version heading
   3. Update link hrefs in the bottom
2. Commit to `dev`
3. Push and check the [GitHub Actions](https://github.com/gu-gridh/queerlit-terms/actions) page to make sure that tests are passing
4. Merge `dev` into `main`
5. Tag the merge commit with the version number prefixed by `v`
6. Push `main` and the tag
7. Deploy to server

**If there are only data changes**, skip the changelog and tag steps (1 and 5).

## Thesaurus library

The [thesaurus.py](qlit/thesaurus.py) module defines what we expect to be doing with the thesaurus in code. It extends the RDFLib [Graph](https://rdflib.readthedocs.io/en/stable/apidocs/rdflib.html#rdflib.graph.Graph) class.

The [simple.py](qlit/simple.py) module redefines this slightly, in order to provide plain-JSON responses for use with the [Queerlit GUI](https://github.com/CDH-DevTeam/queerlit-gui).

## Conversion scripts

1. Add to the `.env` file:
   ```
   INDIR="/path/to/ttls"
   THESAURUSFILE=qlit.nt
   ```
2. Run `python3 build.py`

See [build.py](build.py) and [skos.py](qlit/skos.py).

### Persistence for new identifiers

When there are new terms in the source directory, these will be provided with new canonical ids and reported like:

> Creating new identifiers...
> New id gb58ld43 for stockholmareHBTQI
> New id om71eq87 for sånaHBTQI

The new ids are saved to `qlit.nt` but not in the source files, so the next run will generate new ids again. **You must** manually edit the source files and replace temporary ids with the new canonical ones.

## HTTP server

1. Add to the `.env` file:
   ```
   THESAURUSFILE=qlit.nt
   FLASK_DEBUG=1
   ```
2. Run `flask run`

See [server.py](qlit/server.py).

### HTTP API

| Path                           | Response                                    |
| ------------------------------ | ------------------------------------------- |
| `/`                            | Full RDF data (see _Formats_ below)         |
| `/<name>`                      | RDF data for one term (see _Formats_ below) |
| `/api/term/<name>`             | One term as JSON                            |
| `/api/labels`                  | Labels for all terms, keyed by identifiers  |
| `/api/search?s=<str>`          | Terms matching a partial label              |
| `/api/collections`             | All collections                             |
| `/api/collections/<name>`      | Terms within the collection `<name>`        |
| `/api/roots`                   | All top-level terms                         |
| `/api/narrower?broader=<name>` | Terms narrower than the term `<name>`       |
| `/api/broader?narrower=<name>` | Terms broader than the term `<name>`        |
| `/api/related?other=<name>`    | Terms related to `<name>`                   |

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
