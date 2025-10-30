from time import sleep, time
import requests
import json
import unittest
import argparse
from os import urandom
import sys


class IntegrationTests(unittest.TestCase):
    collectionHeaders = []
    totalAssertions = 0
    test_file_path = 'example/.httptests/test.json'

    @classmethod
    def setResult(cls, totalAssertions):
        cls.totalAssertions += totalAssertions

    def setUp(self):
        self.totalAssertions = 0

    def tearDown(self):
        self.setResult(self.totalAssertions)

    @classmethod
    def tearDownClass(cls):
        print("\n" + "="*60)
        print(f"Total assertions passed: {cls.totalAssertions}")
        print("="*60)

    def check(self):
        # Opening JSON file
        f = open(self.test_file_path)

        data = json.load(f)

        hosts = data["hosts"]
        self.collectionHeaders = data.get("collectionHeaders", [])
        for host in hosts:
            endpoints = hosts[host]
            for endpoint in endpoints:
                self.do_test_endpoint(host, endpoint)

        # Closing file
        f.close()

    # Test each endpoint
    def do_test_endpoint(self, host, endpoint):
        method = endpoint.get("method", "GET")
        paths = endpoint.get("paths")
        sleepReq = endpoint.get("sleep", 0)
        data = endpoint.get("data", None)
        generatePayloadSize = endpoint.get("generatePayloadSize", None)
        if (generatePayloadSize):
            data = urandom(generatePayloadSize)
        expectedStatus = endpoint.get("expectedStatus", 200)
        expectedResponseHeaders = endpoint.get("expectedResponseHeaders", [])
        expectedRequestHeadersToUpstream = endpoint.get("expectedRequestHeadersToUpstream", [])
        additionalRequestHeaders = endpoint.get("additionalRequestHeaders", {})

        for path in paths:
            # Throttle request to prevent limit_req
            sleep(sleepReq)
            print(f"\n  → Testing: {method} {host}{path}")
            response = request(host, path, method, additionalRequestHeaders, data)

            test_name = '%s %s %s (%s)' % (method, host, path, expectedStatus)
            self.do_test_status_code(test_name, expectedStatus, response.status_code)
            self.do_test_response_headers(test_name, expectedResponseHeaders, response.headers)
            self.do_test_request_headers(test_name, expectedRequestHeadersToUpstream, response.text)

    # Status Code
    def do_test_status_code(self, test_name, expectedStatus, status_code):
        with self.subTest(msg='%s => Test Status Code' % test_name):
            if expectedStatus != status_code:
                print(f"    ✗ Status code mismatch!")
                print(f"      Expected: {expectedStatus}")
                print(f"      Got: {status_code}")
                self.fail(f"Status code {status_code} does not match expected {expectedStatus}")
            print(f"    ✓ Status code: {status_code} (expected {expectedStatus})")
            self.totalAssertions += 1

    # Response Headers
    def do_test_response_headers(self, test_name, expectedResponseHeaders, headers):
        with self.subTest(msg='%s => Response Headers' % test_name):
            for header in expectedResponseHeaders:
                headerKey = header[0].lower()
                if (len(header) == 1):
                    if headerKey not in headers:
                        print(f"    ✗ Response header missing: {headerKey}")
                        print(f"      Available headers: {', '.join(headers.keys())}")
                        self.fail(f"Response header '{headerKey}' not found in response")
                    print(f"    ✓ Response header present: {headerKey}")
                    self.totalAssertions += 1
                else:
                    expectedValue = header[1]
                    if headerKey not in headers:
                        print(f"    ✗ Response header missing: {headerKey}")
                        print(f"      Expected value: {expectedValue}")
                        print(f"      Available headers: {', '.join(headers.keys())}")
                        self.fail(f"Response header '{headerKey}' not found in response")
                    elif headers[headerKey] != expectedValue:
                        print(f"    ✗ Response header mismatch: {headerKey}")
                        print(f"      Expected: {expectedValue}")
                        print(f"      Got: {headers[headerKey]}")
                        self.fail(f"Response header '{headerKey}' has value '{headers[headerKey]}', expected '{expectedValue}'")
                    print(f"    ✓ Response header: {headerKey} = {headers[headerKey]}")
                    self.totalAssertions += 1

    # Request Headers to Upstream
    def do_test_request_headers(self, test_name, expectedRequestHeadersToUpstream, text):
        with self.subTest(msg='%s => Request Headers' % test_name):
            if "$collectionheaders" in expectedRequestHeadersToUpstream:
                expectedRequestHeadersToUpstream += self.collectionHeaders
            
            # Try to parse JSON once before processing headers
            try:
                body = json.loads(text)
            except json.JSONDecodeError as e:
                print(f"    ✗ Failed to parse response as JSON")
                print(f"      Error: {e}")
                print(f"      Response text (first 500 chars): {text[:500]}")
                self.fail(f"Response body is not valid JSON: {str(e)}")
                return
            
            for header in expectedRequestHeadersToUpstream:
                headerKey = header[0].lower()
                if headerKey == "$collectionheaders":
                    continue

                if (len(header) == 1):
                    if headerKey not in body.get('headers', {}):
                        print(f"    ✗ Request header not forwarded: {headerKey}")
                        print(f"      Forwarded headers: {', '.join(body.get('headers', {}).keys())}")
                        self.fail(f"Request header '{headerKey}' was not forwarded to upstream")
                    print(f"    ✓ Request header forwarded: {headerKey}")
                    self.totalAssertions += 1
                elif (len(header) == 2):
                    expectedValue = header[1]

                    # Check for deleted headers
                    if expectedValue == "$deleted":
                        if headerKey in body.get('headers', {}):
                            print(f"    ✗ Request header should be removed but was found: {headerKey}")
                            print(f"      Value: {body['headers'][headerKey]}")
                            self.fail(f"Request header '{headerKey}' should be removed but was present with value '{body['headers'][headerKey]}'")
                        print(f"    ✓ Request header removed: {headerKey}")
                        self.totalAssertions += 1
                    else:
                        if headerKey not in body.get('headers', {}):
                            print(f"    ✗ Request header missing: {headerKey}")
                            print(f"      Expected value: {expectedValue}")
                            print(f"      Forwarded headers: {', '.join(body.get('headers', {}).keys())}")
                            self.fail(f"Request header '{headerKey}' not found in forwarded headers")
                        elif body['headers'][headerKey] != expectedValue:
                            print(f"    ✗ Request header mismatch: {headerKey}")
                            print(f"      Expected: {expectedValue}")
                            print(f"      Got: {body['headers'][headerKey]}")
                            self.fail(f"Request header '{headerKey}' has value '{body['headers'][headerKey]}', expected '{expectedValue}'")
                        print(f"    ✓ Request header: {headerKey} = {body['headers'][headerKey]}")
                        self.totalAssertions += 1

def wait_for_service(max_wait=60, check_interval=2):
    """Wait for the service to be ready by checking health"""
    base_url = "http://localhost"
    start_time = time()
    attempt = 0
    
    print(f"\n🔍 Waiting for service to be ready (max {max_wait}s)...")
    
    while time() - start_time < max_wait:
        attempt += 1
        try:
            # Try a simple connection to the service
            response = requests.get(f"{base_url}/", timeout=2)
            print(f"✓ Service is ready! (took {time() - start_time:.1f}s)")
            return True
        except requests.exceptions.ConnectionError:
            elapsed = time() - start_time
            print(f"  Attempt {attempt}: Service not ready yet ({elapsed:.1f}s elapsed)...")
            sleep(check_interval)
        except Exception as e:
            print(f"  Attempt {attempt}: Unexpected error: {e}")
            sleep(check_interval)
    
    print(f"\n❌ ERROR: Service failed to become ready after {max_wait}s")
    print(f"\nTroubleshooting steps:")
    print(f"  1. Check if Docker containers are running: docker ps")
    print(f"  2. Check container logs: docker logs httptests_nginx")
    print(f"  3. Check if port 80 is available: netstat -an | grep :80")
    print(f"  4. Verify nginx configuration is valid")
    return False

def request(host, path, method, additionalRequestHeaders, data):
    headers = {**{'Host': host}, **additionalRequestHeaders}
    base = "http://localhost"
    url = '%s%s' % (base, path)
    
    try:
        r = requests.request(method, url, headers=headers, data=data, timeout=10)
        return r
    except requests.exceptions.ConnectionError as e:
        print(f"\n❌ CONNECTION ERROR")
        print(f"  Target: {method} {url}")
        print(f"  Host header: {host}")
        print(f"  Error: Failed to connect to localhost:80")
        print(f"\n  The service is not responding. Possible causes:")
        print(f"    • Docker containers are not running")
        print(f"    • Nginx failed to start (check config errors)")
        print(f"    • Port 80 is blocked or in use")
        print(f"    • Containers need more time to initialize")
        raise
    except requests.exceptions.Timeout as e:
        print(f"\n❌ TIMEOUT ERROR")
        print(f"  Target: {method} {url}")
        print(f"  The service took too long to respond (>10s)")
        raise
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR")
        print(f"  Target: {method} {url}")
        print(f"  Error: {type(e).__name__}: {e}")
        raise

# Custom test result class that suppresses tracebacks
class CleanTestResult(unittest.TextTestResult):
    def addError(self, test, err):
        """Override to suppress traceback for errors"""
        # Add to errors list but don't store traceback
        self.errors.append((test, None))
        self._mirrorOutput = False
        
    def addFailure(self, test, err):
        """Override to suppress traceback for failures"""
        # Add to failures list but don't store traceback
        self.failures.append((test, None))
        self._mirrorOutput = False
    
    def printErrorList(self, flavour, errors):
        """Override to completely suppress error/failure details"""
        # Don't print anything - our custom error messages are already shown
        pass

class CleanTestRunner(unittest.TextTestRunner):
    """Test runner that uses CleanTestResult"""
    resultclass = CleanTestResult

# Create single test method
setattr(IntegrationTests, "test_endpoints", lambda self: self.check())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run integration tests for HTTP endpoints')
    parser.add_argument(
        '--test-file',
        type=str,
        default='example/.httptests/test.json',
        help='Path to test.json file (default: example/.httptests/test.json)'
    )
    parser.add_argument(
        '--wait-timeout',
        type=int,
        default=60,
        help='Maximum seconds to wait for service to be ready (default: 60)'
    )
    parser.add_argument(
        '--skip-health-check',
        action='store_true',
        help='Skip waiting for service health check'
    )
    args, unittest_args = parser.parse_known_args()
    
    # Wait for service to be ready
    if not args.skip_health_check:
        if not wait_for_service(max_wait=args.wait_timeout):
            print("\n❌ Aborting tests - service is not ready")
            sys.exit(1)
    
    # Set the test file path before running tests
    IntegrationTests.test_file_path = args.test_file
    
    # Run tests with custom runner that suppresses tracebacks
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(IntegrationTests)
    runner = CleanTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
