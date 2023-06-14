# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Changes to data are ignored for the purpose of this changelog.

## [Unreleased]

## [1.3.0] (2023-06-14)

### Changed

- Change structure of the `/api/collections` response

### Added

- A `/api/collections/<name>` route, returning the root terms in a given collection

## [1.2.0] - 2023-03-15

### Added

- `/api/labels` route

### Fixed

- Autocomplete was broken (b2dde71)

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
- An HTTP server that exposes the data as RDF as well as more web-app-friendly JSON

[unreleased]: https://github.com/gu-gridh/queerlit-terms/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/gu-gridh/queerlit-terms/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/gu-gridh/queerlit-terms/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/gu-gridh/queerlit-terms/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/gu-gridh/queerlit-terms/releases/tag/v1.0.0
