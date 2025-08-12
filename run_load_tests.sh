#!/bin/bash

# Load Testing Script for Sarvekshan-AI
# This script runs various load testing scenarios

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_HOST=${API_HOST:-"http://localhost:8000"}
RESULTS_DIR="./results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${GREEN}Starting Load Tests for Sarvekshan-AI${NC}"
echo "API Host: $API_HOST"
echo "Results Directory: $RESULTS_DIR"
echo "Timestamp: $TIMESTAMP"

# Create results directory
mkdir -p "$RESULTS_DIR"

# Function to run a load test scenario
run_load_test() {
    local test_name=$1
    local users=$2
    local spawn_rate=$3
    local duration=$4
    local description=$5
    
    echo -e "\n${YELLOW}Running $test_name${NC}"
    echo "Description: $description"
    echo "Users: $users, Spawn Rate: $spawn_rate/sec, Duration: ${duration}s"
    
    local output_file="$RESULTS_DIR/${test_name}_${TIMESTAMP}.html"
    
    locust \
        --host="$API_HOST" \
        --users="$users" \
        --spawn-rate="$spawn_rate" \
        --run-time="${duration}s" \
        --html="$output_file" \
        --headless \
        --only-summary
    
    echo -e "${GREEN}✓ $test_name completed. Results saved to $output_file${NC}"
}

# Function to check if API is running
check_api_health() {
    echo -e "\n${YELLOW}Checking API health...${NC}"
    
    if curl -f -s "$API_HOST/health" > /dev/null; then
        echo -e "${GREEN}✓ API is healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ API is not responding at $API_HOST${NC}"
        echo "Please ensure the API server is running before running load tests."
        exit 1
    fi
}

# Function to install dependencies
install_dependencies() {
    echo -e "\n${YELLOW}Installing load testing dependencies...${NC}"
    
    if ! command -v locust &> /dev/null; then
        echo "Installing Locust..."
        pip install locust
    else
        echo "Locust is already installed"
    fi
    
    if ! command -v curl &> /dev/null; then
        echo "curl is required but not installed. Please install curl."
        exit 1
    fi
}

# Function to generate summary report
generate_summary() {
    echo -e "\n${YELLOW}Generating summary report...${NC}"
    
    local summary_file="$RESULTS_DIR/load_test_summary_${TIMESTAMP}.md"
    
    cat > "$summary_file" << EOF
# Load Test Summary Report

**Date:** $(date)
**API Host:** $API_HOST
**Test Duration:** Various scenarios

## Test Scenarios

### 1. Light Load Test
- **Users:** 10
- **Duration:** 60 seconds
- **Purpose:** Basic functionality verification

### 2. Normal Load Test
- **Users:** 50
- **Duration:** 300 seconds (5 minutes)
- **Purpose:** Typical usage simulation

### 3. Stress Test
- **Users:** 100
- **Duration:** 180 seconds (3 minutes)
- **Purpose:** High load performance testing

### 4. ML Features Test
- **Users:** 20
- **Duration:** 240 seconds (4 minutes)
- **Purpose:** AI/ML endpoints performance testing

### 5. Spike Test
- **Users:** 200
- **Duration:** 60 seconds
- **Purpose:** Sudden load spike handling

## Results

Individual test results are available in the following files:
EOF

    # List all result files
    for file in "$RESULTS_DIR"/*_${TIMESTAMP}.html; do
        if [ -f "$file" ]; then
            echo "- $(basename "$file")" >> "$summary_file"
        fi
    done
    
    cat >> "$summary_file" << EOF

## Recommendations

1. Review response times for all endpoints
2. Check error rates and identify bottlenecks
3. Monitor resource usage during peak loads
4. Optimize slow endpoints identified in the tests
5. Consider scaling strategies for production deployment

## Next Steps

1. Run tests against production-like environment
2. Implement performance monitoring
3. Set up automated performance regression testing
4. Optimize database queries and caching
5. Consider implementing rate limiting and circuit breakers
EOF

    echo -e "${GREEN}✓ Summary report generated: $summary_file${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}Sarvekshan-AI Load Testing Suite${NC}"
    echo "=================================="
    
    # Install dependencies
    install_dependencies
    
    # Check API health
    check_api_health
    
    # Run test scenarios
    echo -e "\n${YELLOW}Starting load test scenarios...${NC}"
    
    # 1. Light load test - basic functionality
    run_load_test "light_load" 10 2 60 "Basic functionality verification with light load"
    
    # 2. Normal load test - typical usage
    run_load_test "normal_load" 50 5 300 "Typical usage simulation with moderate load"
    
    # 3. Stress test - high load
    run_load_test "stress_test" 100 10 180 "High load stress testing"
    
    # 4. ML features focused test
    run_load_test "ml_features" 20 3 240 "AI/ML endpoints performance testing"
    
    # 5. Spike test - sudden load increase
    run_load_test "spike_test" 200 20 60 "Sudden load spike handling test"
    
    # Generate summary
    generate_summary
    
    echo -e "\n${GREEN}All load tests completed successfully!${NC}"
    echo -e "Results are available in: ${YELLOW}$RESULTS_DIR${NC}"
    echo -e "Summary report: ${YELLOW}$RESULTS_DIR/load_test_summary_${TIMESTAMP}.md${NC}"
}

# Handle script arguments
case "${1:-}" in
    "light")
        install_dependencies
        check_api_health
        run_load_test "light_load" 10 2 60 "Basic functionality verification"
        ;;
    "normal")
        install_dependencies
        check_api_health
        run_load_test "normal_load" 50 5 300 "Normal load testing"
        ;;
    "stress")
        install_dependencies
        check_api_health
        run_load_test "stress_test" 100 10 180 "Stress testing"
        ;;
    "ml")
        install_dependencies
        check_api_health
        run_load_test "ml_features" 20 3 240 "ML features testing"
        ;;
    "spike")
        install_dependencies
        check_api_health
        run_load_test "spike_test" 200 20 60 "Spike testing"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [scenario]"
        echo ""
        echo "Scenarios:"
        echo "  light   - Light load test (10 users, 60s)"
        echo "  normal  - Normal load test (50 users, 300s)"
        echo "  stress  - Stress test (100 users, 180s)"
        echo "  ml      - ML features test (20 users, 240s)"
        echo "  spike   - Spike test (200 users, 60s)"
        echo "  (none)  - Run all scenarios"
        echo ""
        echo "Environment variables:"
        echo "  API_HOST - API server URL (default: http://localhost:8000)"
        ;;
    *)
        main
        ;;
esac

