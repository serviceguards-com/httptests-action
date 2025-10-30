# HTTPTests Runner Action

Reusable GitHub Action that runs integration tests for a specified `.httptests/` test suite, generates Docker Compose configurations, and executes integration tests against your Nginx configurations.

## Features

- 🐳 Generates `docker-compose.yml` from `config.yml` for the test suite
- 🧪 Runs integration tests with isolated Docker environment
- 🧹 Automatic cleanup after test execution
- 📦 Ready for GitHub Marketplace distribution
- 🔄 Matrix strategy support for testing multiple suites in parallel
- 🎯 Automatic `X-Upstream-Target` header injection for precise proxy validation

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
  additional_ports:
    - 5001
    - 8080
  network_aliases:
    - store
    - api-backend

nginx:
  environment:
    ENV_VAR_1: value1
    ENV_VAR_2: value2
```

#### Supported Fields

**`mock.http_port`** (integer, optional)
- HTTP port number for the mock service to listen on
- **Default: `80`** - Always available by default
- Legacy field `port` is also supported and maps to `http_port`
- Only override if you need to change the primary HTTP port
- Example: `8080`, `3000`

**`mock.https_port`** (integer, optional)
- HTTPS port number for the mock service to listen on
- **Default: `443`** - Always available by default
- Only override if you need to change the primary HTTPS port
- Example: `8443`

**`mock.additional_ports`** (list, optional)
- Additional ports beyond 80 and 443 to make the mock service accessible on
- Uses socat port forwarders with the same network aliases
- The mock service always listens on ports 80 (HTTP) and 443 (HTTPS) by default
- Use this when your nginx config proxies to non-standard ports like 5001, 8080, etc.
- Example: `[5001, 8080]`

**`mock.network_aliases`** (list)
- Network aliases for the mock HTTP echo service
- Allows Nginx to proxy requests to these hostnames
- All aliases are accessible on all configured ports (http_port, https_port, and additional_ports)
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
3. **Header Injection**: Automatically adds `X-Upstream-Target` headers to nginx configs for upstream validation
4. **Generation**: Generates `docker-compose.yml` from `config.yml`
5. **Build**: Builds the Nginx container from the Dockerfile in the parent directory
6. **Start**: Starts mock and Nginx services with isolated Docker Compose project name
7. **Test**: Runs `main.py` against the `test.json` file
8. **Cleanup**: Tears down containers and removes volumes

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
  
  # Optional: Port forwarders (if additional_ports configured)
  mock-forwarder-5001:
    container_name: httptests_forwarder_5001
    image: alpine/socat:latest
    command: "TCP-LISTEN:5001,fork,reuseaddr TCP:mock:80"
    networks:
      default:
        aliases:
          - <your-network-aliases>
    depends_on:
      - mock
  
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
      # - mock-forwarder-5001  # Added if additional_ports configured
    environment:
      <your-environment-variables>
```

When `additional_ports` are configured, the action automatically creates socat forwarder services that listen on the additional ports and forward traffic to the main mock service. This allows the same service to be accessible on multiple ports using the same network aliases.

## Automatic Upstream Target Header Injection

HTTPTests includes an automatic header injection feature that adds `X-Upstream-Target` headers to your nginx configurations. This enables precise validation that your proxy is connecting to the exact intended upstream, even when multiple similar services exist in the Docker network.

### How It Works

Before building the Docker containers, the action runs `add_upstream_headers.py` which:

1. **Scans** all `.conf` files in your httptests directory
2. **Detects** `proxy_pass` directives using regex pattern matching
3. **Extracts** the upstream URL (e.g., `http://backend:5001/`)
4. **Injects** a `proxy_set_header X-Upstream-Target "<url>";` line immediately after each `proxy_pass`
5. **Preserves** indentation and formatting
6. **Skips** if the header already exists (idempotent operation)

### Example

**Before injection:**
```nginx
location /api/ {
    proxy_pass http://backend:5001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

**After automatic injection:**
```nginx
location /api/ {
    proxy_pass http://backend:5001/;
    proxy_set_header X-Upstream-Target "backend:5001";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Testing Upstream Destinations

Once the header is injected, you can validate it in your tests:

```json
{
    "paths": ["/api/users"],
    "method": "GET",
    "expectedStatus": 200,
    "expectedRequestHeadersToUpstream": [
        ["X-Upstream-Target", "backend:5001"]
    ]
}
```

### Why This Matters

Consider a scenario where multiple upstreams exist:
- `backend:5001` (correct destination)
- `backend:9999` (wrong port)
- `different-host:5001` (wrong host)

All three may respond to HTTP requests, but only the correct one will have the matching `X-Upstream-Target` header value. This guarantees your test validates the **exact proxy destination**, not just "some service responded."

**Script features:**
- ✅ Idempotent (safe to run multiple times)
- ✅ Preserves indentation
- ✅ Handles multiple `proxy_pass` directives per file
- ✅ Works with any nginx configuration file (`.conf`)

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

