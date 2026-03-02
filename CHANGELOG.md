# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and this project follows semantic versioning.

## [Unreleased]
### Added
- MySQLStore backend using SQLAlchemy ORM.
- Docker Compose file for local MySQL.
- Example MySQL usage and config.
- MySQL RBAC helper methods (users, roles, conversation access).
- Added authorize_or_raise helper for RBAC enforcement.
- Added require_access helper module and MySQL-backed pytest suite.
### Changed
- Removed FileStore in favor of database-backed stores only.
- Removed SQLiteStore to make MySQL the only supported backend.

## [0.1.0] - 2026-02-23
### Added
- Initial ConvoSaver package with file and SQLite backends.
- Policy support for max messages, max chars, and regex redaction.
- Conversation export helpers and basic examples.
- Project documentation via README and agents.md.
