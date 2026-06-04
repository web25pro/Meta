# Performance Testing with Locust

## Overview

This directory contains performance tests for the LPanda Platform using Locust.

## Installation

Install locust:
`ash
pip install locust==2.20.0
# or
poetry add locust==2.20.0 --group dev
`

## Running Tests

### Interactive Mode (Web UI)
`ash
locust -f tests/performance/locustfile.py --host=http://localhost:8000
`
Then open http://localhost:8089 in your browser.

### Headless Mode (Command Line)

**Smoke Test** (10 users, 1 minute):
`ash
locust -f tests/performance/locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 1m --headless
`

**Load Test** (100 users, 5 minutes):
`ash
locust -f tests/performance/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless
`

**Stress Test** (1000 users, 10 minutes):
`ash
locust -f tests/performance/locustfile.py --host=http://localhost:8000 --users 1000 --spawn-rate 100 --run-time 10m --headless
`

## Performance Targets

From the design document:
- API response time p95 < 1 second
- Error rate < 1%
- Support 1000 concurrent users
- Database query performance optimized

## Test Scenarios

The locustfile includes two user types:
1. **LPandaPlatformUser**: Regular users (90% of traffic)
2. **AdminUser**: Admin users (10% of traffic)

**Validates: Requirements 1.1 - Testing Infrastructure**
