# HTTPTests Runner Action

Reusable GitHub Action that discovers `.httptests/` test suites in your repository, generates Docker Compose configurations, and executes integration tests against your Nginx configurations.

## Features

- 🔍 Automatically discovers all `.httptests/` directories in your repository
- 🐳 Generates `docker-compose.yml` from `config.yml` for each test suite
- 🧪 Runs integration tests with isolated Docker environments
- 🧹 Automatic cleanup after test execution
- 📦 Ready for GitHub Marketplace distribution

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
          working-directory: .
          python-version: '3.x'
```

### Using from GitHub Marketplace (when published)

```yaml
- name: Run HTTPTests
  uses: your-username/httptests-action@v1
  with:
    working-directory: .
    python-version: '3.x'
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `working-directory` | Root directory to start scanning for `.httptests/` folders | No | `.` |
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

1. **Discovery**: Scans the `working-directory` for all `.httptests/` folders
2. **Generation**: For each suite, generates `docker-compose.yml` from `config.yml`
3. **Build**: Builds the Nginx container from the Dockerfile in the parent directory
4. **Start**: Starts mock and Nginx services with isolated Docker Compose project names
5. **Test**: Runs `main.py` against the `test.json` file
6. **Cleanup**: Tears down containers and removes volumes

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

The action automatically processes **all** `.httptests/` directories found in your repository. Each suite runs in isolation with its own Docker Compose project to avoid conflicts.

Example output:
```
Scanning for .httptests under: .
Found: ./service-a/.httptests
Found: ./service-b/.httptests

=== Processing suite: ./service-a/.httptests ===
Generating compose file...
Bringing up services for httptests_service_a...
Running tests...
Tearing down services...

=== Processing suite: ./service-b/.httptests ===
Generating compose file...
Bringing up services for httptests_service_b...
Running tests...
Tearing down services...
```

## Troubleshooting

### No .httptests directories found

Ensure your test suites are named exactly `.httptests` (with the leading dot) and contain at least a `test.json` file.

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

