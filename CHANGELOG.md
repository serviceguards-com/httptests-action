# Changelog

All notable changes to HTTPTests will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-30

### Added
- Initial release of HTTPTests GitHub Action
- Auto-discovery of `.httptests` test suites
- Docker Compose generation from `config.yml`
- Integration test runner with detailed output
- Support for multiple test suites in a single repository
- Isolated Docker environments per test suite
- Collection headers support
- Request/Response validation (status codes, headers)
- Upstream request header validation
- Mock HTTP echo service integration
- Comprehensive documentation and examples

### Features
- **Auto-Discovery**: Scans repository for all `.httptests` directories
- **Docker Isolation**: Each test suite runs in isolated environment
- **Multi-Service**: Support for complex service architectures
- **Flexible Configuration**: YAML-based Docker setup, JSON-based tests
- **CI/CD Ready**: Native GitHub Actions integration

### Documentation
- Main README with quick start guide
- Technical documentation (TECHNICAL.md)
- Example projects for multiple use cases
- Contributing guidelines
- Code of Conduct

[1.0.0]: https://github.com/serviceguards-com/httptests-action/releases/tag/v1.0.0

