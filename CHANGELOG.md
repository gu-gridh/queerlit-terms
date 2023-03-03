# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Changes to data are ignored for the purpose of this changelog.

## [1.1.0] - 2023-03-03

### Added

- Collections are now in the data including the RDF server output, and there is now an /api/collections endpoint

### Changed

- Autocomplete matches are now scored and sorted by relevance, based on which label matches the search words and
- Other list routes are sorted alphabetically by prefLabel

### Fixed

- Restore case-insensitive autocomplete

## [1.0.0] - 2023-01-30

This was the latest commit before the public release on Feb 14, ignoring data updates.

Features:

- A build script that compiles multiple RDF/SKOS files (terms) to one (thesaurus).
- An HTTP server that exposes the data as RDF as well as more web-app-friendly JSON.
