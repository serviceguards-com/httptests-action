from time import sleep
import requests
import json
import unittest
import argparse
from os import urandom


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
            self.assertEqual(expectedStatus, status_code)
            print(f"    ✓ Status code: {status_code} (expected {expectedStatus})")
            self.totalAssertions += 1

    # Response Headers
    def do_test_response_headers(self, test_name, expectedResponseHeaders, headers):
        with self.subTest(msg='%s => Response Headers' % test_name):
            for header in expectedResponseHeaders:
                headerKey = header[0].lower()
                if (len(header) == 1):
                    self.assertTrue(headerKey in headers)
                    print(f"    ✓ Response header present: {headerKey}")
                    self.totalAssertions += 1
                else:
                    expectedValue = header[1]
                    self.assertEqual(headers[headerKey], expectedValue)
                    print(f"    ✓ Response header: {headerKey} = {headers[headerKey]}")
                    self.totalAssertions += 1

    # Request Headers to Upstream
    def do_test_request_headers(self, test_name, expectedRequestHeadersToUpstream, text):
        with self.subTest(msg='%s => Request Headers' % test_name):
            if "$collectionheaders" in expectedRequestHeadersToUpstream:
                expectedRequestHeadersToUpstream += self.collectionHeaders
            for header in expectedRequestHeadersToUpstream:
                headerKey = header[0].lower()
                if headerKey == "$collectionheaders":
                    continue

                body = json.loads(text)

                if (len(header) == 1):
                    self.assertTrue(headerKey in body['headers'])
                    print(f"    ✓ Request header forwarded: {headerKey}")
                    self.totalAssertions += 1
                elif (len(header) == 2):
                    expectedValue = header[1]

                    # Check for deleted headers
                    if expectedValue == "$deleted":
                        self.assertTrue(headerKey not in body['headers'])
                        print(f"    ✓ Request header removed: {headerKey}")
                        self.totalAssertions += 1
                    else:
                        self.assertEqual(body['headers'][headerKey], expectedValue)
                        print(f"    ✓ Request header: {headerKey} = {body['headers'][headerKey]}")
                        self.totalAssertions += 1

def request(host, path, method, additionalRequestHeaders, data):
    headers = {**{'Host': host}, **additionalRequestHeaders}
    base = "http://localhost"
    r = requests.request(method, '%s%s' % (base, path), headers=headers, data=data)
    return r

# Create single test method
setattr(IntegrationTests, "test_endpoints", lambda self: self.check())

if __name__ == '__main__':
    import sys
    parser = argparse.ArgumentParser(description='Run integration tests for HTTP endpoints')
    parser.add_argument(
        '--test-file',
        type=str,
        default='example/.httptests/test.json',
        help='Path to test.json file (default: example/.httptests/test.json)'
    )
    args, unittest_args = parser.parse_known_args()
    
    # Set the test file path before running tests
    IntegrationTests.test_file_path = args.test_file
    
    # Pass remaining args to unittest
    sys.argv = ['main.py'] + unittest_args
    unittest.main(verbosity=2)
