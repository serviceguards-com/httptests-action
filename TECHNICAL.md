# HTTPTests Runner Action

Reusable GitHub Action that runs integration tests for a specified `.httptests/` test suite, generates Docker Compose configurations, and executes integration tests against your Nginx configurations.

## Features

- 🐳 Generates `docker-compose.yml` from `config.yml` for the test suite
- 🧪 Runs integration tests with isolated Docker environment
- 🧹 Automatic cleanup after test execution
- 📦 Ready for GitHub Marketplace distribution
- 🔄 Matrix strategy support for testing multiple suites in parallel

## Usage

### Basic Example

```yaml
name: HTTPTests
on:
  push:
  pull_request:

jobs:
  run-httptests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run HTTPTests
        uses: ./httptests-action  # Reference the action from your repository
        with:
          httptests-directory: ./your-service
          python-version: '3.x'
```

### Using from GitHub Marketplace (when published)

```yaml
- name: Run HTTPTests
  uses: your-username/httptests-action@v2
  with:
    httptests-directory: ./your-service
    python-version: '3.x'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `httptests-directory` | Path to directory containing `.httptests` folder | Yes | - |
| `python-version` | Python version to use for test execution | No | `3.x` |

## Expected Repository Structure

```
repo/
├── httptests-action/
│   ├── action.yml                  # This GitHub Action
│   ├── generate_docker_compose.py  # Compose generator
│   └── main.py                     # Test runner script
├── your-service/
│   ├── Dockerfile                  # Nginx container definition
│   ├── nginx.conf                  # Nginx configuration
│   └── .httptests/
│       ├── config.yml              # Docker Compose configuration
│       └── test.json               # Test definitions
└── another-service/
    ├── Dockerfile
    ├── nginx.conf
    └── .httptests/
        ├── config.yml
        └── test.json
```

## Configuration Format

### `config.yml`

The `config.yml` file defines how Docker Compose services should be configured:

```yaml
mock:
  network_aliases:
    - store
    - api-backend

nginx:
  environment:
    ENV_VAR_1: value1
    ENV_VAR_2: value2
```

#### Supported Fields

**`mock.network_aliases`** (list)
- Network aliases for the mock HTTP echo service
- Allows Nginx to proxy requests to these hostnames
- Example: `store`, `api-backend`, `payment-service`

**`nginx.environment`** (dict or list)
- Environment variables passed to the Nginx container
- Can be specified as key-value pairs (dict) or as list of `KEY=value` strings
- Useful for dynamic configuration

### `test.json`

Define your HTTP test cases in `test.json`:

```json
{
  "collectionHeaders": [
    ["X-Request-Id"],
    ["X-Path"]
  ],
  "hosts": {
    "example.localhost": [
      {
        "paths": ["/api/hello"],
        "method": "GET",
        "expectedStatus": 200,
        "expectedResponseHeaders": [
          ["Content-Type", "application/json"]
        ]
      }
    ]
  }
}
```

See the main [README.md](README.md) for complete test configuration documentation.

## How It Works

1. **Discovery**: Looks for `.httptests/` folder within the specified directory
2. **Validation**: Verifies the `.httptests/` directory exists and contains `test.json`
3. **Generation**: Generates `docker-compose.yml` from `config.yml`
4. **Build**: Builds the Nginx container from the Dockerfile in the parent directory
5. **Start**: Starts mock and Nginx services with isolated Docker Compose project name
6. **Test**: Runs `main.py` against the `test.json` file
7. **Cleanup**: Tears down containers and removes volumes

## Generated Docker Compose Structure

The action generates a `docker-compose.yml` with the following structure:

```yaml
version: "3.9"
services:
  mock:
    container_name: httptests_mock
    image: mendhak/http-https-echo:18
    environment:
      - HTTP_PORT=80
      - HTTPS_PORT=443
    networks:
      default:
        aliases:
          - <your-network-aliases>
  
  nginx:
    container_name: httptests_nginx
    build:
      context: <parent-directory>
      dockerfile: Dockerfile
    ports:
      - "80:80"
    networks:
      - default
    depends_on:
      - mock
    environment:
      <your-environment-variables>
```

## Requirements

- **Docker Compose V2**: The action uses `docker compose` command (not `docker-compose`)
- **Ubuntu Runner**: Recommended to use `ubuntu-latest` which includes Docker
- **Repository Structure**: Action must be in `httptests-action/` directory with `main.py` test runner

## Multiple Test Suites

To test multiple `.httptests/` directories, use a matrix strategy. Each suite runs in isolation with its own Docker Compose project to avoid conflicts.

Example workflow:
```yaml
name: HTTPTests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        test-suite:
          - ./service-a
          - ./service-b
          - ./service-c
    steps:
      - uses: actions/checkout@v4
      - uses: your-username/httptests-action@v2
        with:
          httptests-directory: ${{ matrix.test-suite }}
```

Each test suite will run in parallel as a separate job with its own isolated Docker environment.

## Troubleshooting

### Directory not found

Ensure the path specified in `httptests-directory` exists. The action will automatically look for a `.httptests` folder within that directory.

### .httptests directory not found

Ensure the specified directory contains a `.httptests` folder (with the leading dot).

### Missing test.json

The `.httptests` directory must contain a `test.json` file with test definitions.

### Dockerfile not found

The action expects a `Dockerfile` in the parent directory of each `.httptests/` folder. Check your repository structure.

### Tests failing to connect

By default, the action waits 5 seconds for services to start. If your services need more time, you may need to add health checks to your Dockerfile.

## License

This action is designed for integration testing of Nginx proxy configurations and API gateways.

## Contributing

Contributions are welcome! Please ensure:
- The action files remain in the `httptests-action/` directory
- All tests pass before submitting a PR
- Documentation is updated for any new features

