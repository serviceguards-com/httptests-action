# Nginx Integration Test Suite

This project contains an automated integration test suite for testing Nginx proxy configurations and routing behavior.

## Overview

The test suite validates that Nginx correctly:
- Routes requests to appropriate upstream services
- Modifies request headers when proxying to upstream services
- Returns expected HTTP status codes
- Handles various request scenarios (GET, POST, large payloads, etc.)

## Architecture

The test suite consists of three main components:

### 1. Test Runner (`main.py`)
A Python unittest-based test runner that:
- Reads test configurations from `test.json`
- Makes HTTP requests to the Nginx proxy
- Validates responses and headers
- Tracks assertion counts for reporting

### 2. Test Configuration (`test.json`)
A JSON configuration file that defines:
- **Collection Headers**: Common headers to include in all requests
- **Hosts**: Different hostnames to test against
- **Endpoints**: Specific paths and their expected behaviors
- **Test Parameters**: Expected status codes, headers, request data, etc.

### 3. Docker Environment (`docker-compose.yml`)
A containerized test environment with:
- **Mock Service**: HTTP echo server that responds with request details
- **Nginx API**: The Nginx proxy being tested (configured via environment variables)

## Test Configuration Format

The `test.json` file uses the following structure:

```json
{
    "collectionHeaders": [
        ["X-Request-Id"],
        ["X-Path"],
        ["X-Verb"],
        ["X-QS"]
    ],
    "hosts": {
        "api.domain.com": [
            {
                "paths": ["/store/product_list"],
                "method": "GET",
                "expectedStatus": 200,
                "additionalRequestHeaders": {"X-Cache-Status": "HIT"},
                "expectedRequestHeadersToUpstream": [
                    ["$collectionHeaders"],
                    ["X-Cache-Status", "HIT"],
                    ["X-Forwarded-For"],
                    ["X-Proxy-Pass", "store"]
                ]
            }
        ]
    }
}
```

### Configuration Options

- **`collectionHeaders`**: Headers automatically added to all requests
- **`paths`**: Array of URL paths to test
- **`method`**: HTTP method (defaults to GET)
- **`expectedStatus`**: Expected HTTP status code (defaults to 200)
- **`additionalRequestHeaders`**: Headers to add to the test request
- **`expectedRequestHeadersToUpstream`**: Headers expected in the upstream request
- **`data`**: Request body data for POST requests
- **`generatePayloadSize`**: Generate random data of specified size (bytes)
- **`sleep`**: Delay between requests (seconds)

### Special Header Values

- **`$collectionHeaders`**: Expands to all collection headers
- **`$deleted`**: Expects the header to be absent from upstream request

## Running the Tests

### Prerequisites

- Docker and Docker Compose
- Python 3.x with `requests` library

### Setup

1. **Start the test environment:**
   ```bash
   docker-compose up -d
   ```

2. **Run the tests:**
   ```bash
   python main.py
   ```

### Test Output

The test runner provides detailed output including:
- Individual test results for each endpoint
- Status code validations
- Header presence and value checks
- Total assertion count

Example output:
```
test_endpoints (__main__.IntegrationTests) ... 
  GET api.domain.com /store/product_list (200) => Test Status Code ... ok
  GET api.domain.com /store/product_list (200) => Request Headers ... ok
Total assertions: 15
```

## Test Scenarios

The test suite validates various scenarios:

1. **Basic Routing**: Ensures requests reach the correct upstream services
2. **Header Modification**: Verifies Nginx adds/modifies headers when proxying
3. **Status Code Handling**: Tests different HTTP status codes (200, 403, 404, 413)
4. **Request Methods**: Supports GET, POST, and other HTTP methods
5. **Large Payloads**: Tests handling of large request bodies
6. **Rate Limiting**: Includes sleep delays to test rate limiting behavior
7. **Header Deletion**: Ensures certain headers are removed from upstream requests

## Mock Service

The mock service (`mendhak/http-https-echo`) responds to all requests by echoing back:
- Request headers
- Request body
- Request method and path
- Other request metadata

This allows the test suite to verify exactly what headers and data Nginx forwards to upstream services.

## Customization

To test different Nginx configurations:

1. **Update `test.json`**: Modify the test cases to match your endpoints
2. **Update `docker-compose.yml`**: Configure environment variables for your Nginx setup
3. **Run tests**: Execute `python main.py` to validate your configuration

## Use Cases

This test suite is ideal for:
- Validating Nginx proxy configurations
- Testing API gateway routing rules
- Verifying header transformation logic
- Regression testing after Nginx configuration changes
- Load balancer configuration validation
