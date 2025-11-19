# Changelog

All notable changes to HTTPTests will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-30

### Changed
- **BREAKING**: Removed auto-discovery of `.httptests` directories
  - Now requires explicit `httptests-directory` input parameter
  - Processes only a single `.httptests` folder per action run
  - Removed `working-directory` input parameter
  - For multiple test suites, use separate workflow jobs or matrix strategy

### Migration Guide
Before (v1.x):
```yaml
- uses: serviceguards-com/httptests-action@latest
  with:
    working-directory: ./services
```

After (v2.0):
```yaml
- uses: serviceguards-com/httptests-action@latest2
  with:
    httptests-directory: ./services/api-gateway
```

The action will automatically discover the `.httptests` folder within the specified directory.

For multiple test suites, use a matrix strategy:
```yaml
strategy:
  matrix:
    test-suite:
      - ./service-a
      - ./service-b
steps:
  - uses: serviceguards-com/httptests-action@latest2
    with:
      httptests-directory: ${{ matrix.test-suite }}
```

## [1.1.0] - 2025-10-30

### Added
- **Service Health Check**: Automatic health check with configurable timeout before running tests
  - Polls service endpoint until ready (default 60s timeout)
  - Shows progress with attempt counters and elapsed time
  - Provides troubleshooting steps if service fails to start
  - New CLI arguments: `--wait-timeout` and `--skip-health-check`

### Improved
- **Error Logging**: Significantly enhanced error messages throughout
  - Connection errors now show target URL, host header, and possible causes
  - Timeout errors clearly indicate slow response times
  - Status code mismatches show expected vs actual values
  - Missing headers show available headers for easier debugging
  - Header value mismatches show expected vs actual values
  - JSON parsing errors display response content for investigation
- **Docker Error Handling**: Better visibility into container failures
  - Automatic container log dumps when tests fail
  - Shows both nginx and mock container logs
  - Displays container status on startup failures
  - Clear error messages for docker-compose generation failures
- **Progress Indicators**: Added visual feedback with emojis
  - 📦 Starting Docker services...
  - 🧪 Running tests...
  - 🧹 Cleaning up...
  - ✓/✗ for success/failure states

### Fixed
- **Connection Refused Error**: Tests now wait for services to be ready before running
  - Eliminates race condition where tests started before containers were ready
  - Retry logic with exponential backoff ensures reliable startup
  - Timeout prevents infinite waiting

### Changed
- Requests now have 10s timeout to prevent hanging
- Better error context in all exception handlers
- More informative test output with detailed assertion failures

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

