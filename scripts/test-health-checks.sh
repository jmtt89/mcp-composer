#!/bin/bash

# Health Check Testing Script for MCP Composer
# This script tests all health check endpoints

set -e

# Configuration
BASE_URL=${MCP_COMPOSER_URL:-"http://localhost:8000"}
API_PREFIX="/api/v1/health"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to test an endpoint
test_endpoint() {
    local endpoint=$1
    local description=$2
    local expected_status=${3:-200}
    
    echo -e "${YELLOW}Testing ${endpoint} - ${description}${NC}"
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "${BASE_URL}${API_PREFIX}${endpoint}")
    body=$(echo "$response" | sed -E 's/HTTPSTATUS\:[0-9]{3}$//')
    status=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status" -eq "$expected_status" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Status: $status"
        echo "Response: $body" | jq '.' 2>/dev/null || echo "Response: $body"
    else
        echo -e "${RED}✗ FAIL${NC} - Expected: $expected_status, Got: $status"
        echo "Response: $body"
        return 1
    fi
    echo
}

# Function to wait for service to be ready
wait_for_service() {
    echo -e "${YELLOW}Waiting for service to be available...${NC}"
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s "${BASE_URL}${API_PREFIX}/live" > /dev/null 2>&1; then
            echo -e "${GREEN}Service is available!${NC}"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts - Service not ready yet..."
        sleep 2
        ((attempt++))
    done
    
    echo -e "${RED}Service failed to become available after $max_attempts attempts${NC}"
    return 1
}

# Function to test startup sequence
test_startup_sequence() {
    echo -e "${YELLOW}Testing startup sequence...${NC}"
    
    # Test startup probe multiple times to simulate behavior
    for i in {1..3}; do
        echo "Startup check attempt $i:"
        test_endpoint "/startup" "Startup Probe"
        sleep 1
    done
}

# Function to test all health endpoints
test_all_endpoints() {
    echo -e "${YELLOW}=== MCP Composer Health Check Tests ===${NC}"
    echo "Base URL: $BASE_URL"
    echo
    
    # Test basic health endpoint
    test_endpoint "" "Basic Health Check"
    test_endpoint "/live" "Liveness Probe"
    test_endpoint "/ready" "Readiness Probe" 
    test_endpoint "/startup" "Startup Probe"
}

# Function to simulate failure scenarios
test_failure_scenarios() {
    echo -e "${YELLOW}=== Testing Failure Scenarios ===${NC}"
    
    # Test non-existent endpoint
    echo -e "${YELLOW}Testing non-existent endpoint${NC}"
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "${BASE_URL}${API_PREFIX}/nonexistent" || true)
    status=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [ "$status" -eq "404" ]; then
        echo -e "${GREEN}✓ PASS${NC} - Correctly returns 404 for non-existent endpoint"
    else
        echo -e "${RED}✗ FAIL${NC} - Expected 404, got $status"
    fi
    echo
}

# Function to monitor health over time
monitor_health() {
    local duration=${1:-60}
    echo -e "${YELLOW}Monitoring health for $duration seconds...${NC}"
    
    local end_time=$(($(date +%s) + duration))
    while [ $(date +%s) -lt $end_time ]; do
        local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
        echo -n "[$timestamp] "
        
        if curl -s "${BASE_URL}${API_PREFIX}/ready" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Ready${NC}"
        else
            echo -e "${RED}✗ Not Ready${NC}"
        fi
        
        sleep 5
    done
}

# Main execution
main() {
    case "${1:-all}" in
        "wait")
            wait_for_service
            ;;
        "startup")
            test_startup_sequence
            ;;
        "all")
            wait_for_service
            test_all_endpoints
            ;;
        "failures")
            test_failure_scenarios
            ;;
        "monitor")
            monitor_health "${2:-60}"
            ;;
        "help"|"-h"|"--help")
            echo "Usage: $0 [command] [options]"
            echo "Commands:"
            echo "  all       - Run all health check tests (default)"
            echo "  wait      - Wait for service to become available"
            echo "  startup   - Test startup sequence"
            echo "  failures  - Test failure scenarios"
            echo "  monitor [duration] - Monitor health for specified seconds (default: 60)"
            echo "  help      - Show this help message"
            echo
            echo "Environment variables:"
            echo "  MCP_COMPOSER_URL - Base URL for the service (default: http://localhost:8000)"
            ;;
        *)
            echo "Unknown command: $1. Use 'help' for usage information."
            exit 1
            ;;
    esac
}

# Check if required tools are available
if ! command -v curl &> /dev/null; then
    echo -e "${RED}Error: curl is required but not installed${NC}"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    echo -e "${YELLOW}Warning: jq not found. JSON responses will not be pretty-printed${NC}"
fi

# Run main function with all arguments
main "$@"
