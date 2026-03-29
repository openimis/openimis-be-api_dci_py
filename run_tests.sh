#!/bin/bash
# Script to run DCI API tests
# Usage: ./run_tests.sh [options]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  DCI API Test Runner${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Default values
VERBOSE=1
KEEPDB=""
PARALLEL=""
COVERAGE=""
TEST_PATH="api_dci.tests"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--verbose)
            VERBOSE=2
            shift
            ;;
        -vv|--very-verbose)
            VERBOSE=3
            shift
            ;;
        -k|--keepdb)
            KEEPDB="--keepdb"
            shift
            ;;
        -p|--parallel)
            PARALLEL="--parallel=4"
            shift
            ;;
        -c|--coverage)
            COVERAGE=1
            shift
            ;;
        --sync-search)
            TEST_PATH="api_dci.tests.test_sync_search"
            shift
            ;;
        --subscription)
            TEST_PATH="api_dci.tests.test_subscription"
            shift
            ;;
        --person-detail)
            TEST_PATH="api_dci.tests.test_person_detail"
            shift
            ;;
        -h|--help)
            echo "Usage: ./run_tests.sh [options]"
            echo ""
            echo "Options:"
            echo "  -v, --verbose          Verbose output (level 2)"
            echo "  -vv, --very-verbose    Very verbose output (level 3)"
            echo "  -k, --keepdb           Keep test database between runs"
            echo "  -p, --parallel         Run tests in parallel (4 processes)"
            echo "  -c, --coverage         Run with coverage report"
            echo "  --sync-search          Run only sync search tests"
            echo "  --subscription         Run only subscription tests"
            echo "  --person-detail        Run only person detail tests"
            echo "  -h, --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./run_tests.sh                    # Run all tests"
            echo "  ./run_tests.sh -v -k              # Verbose with keepdb"
            echo "  ./run_tests.sh -c                 # With coverage"
            echo "  ./run_tests.sh --sync-search      # Only sync search tests"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}Error: manage.py not found${NC}"
    echo "Please run this script from the OpenIMIS backend root directory"
    exit 1
fi

# Check if api_dci module exists
if [ ! -d "api_dci" ]; then
    echo -e "${RED}Error: api_dci module not found${NC}"
    echo "Make sure you're in the correct OpenIMIS installation"
    exit 1
fi

echo -e "${YELLOW}Configuration:${NC}"
echo "  Test path: $TEST_PATH"
echo "  Verbosity: $VERBOSE"
echo "  Keep DB: ${KEEPDB:-no}"
echo "  Parallel: ${PARALLEL:-no}"
echo "  Coverage: ${COVERAGE:-no}"
echo ""

# Run tests with or without coverage
if [ "$COVERAGE" = "1" ]; then
    echo -e "${YELLOW}Running tests with coverage...${NC}"
    echo ""

    coverage run --source='api_dci' manage.py test "$TEST_PATH" \
        --verbosity=$VERBOSE \
        $KEEPDB \
        $PARALLEL

    echo ""
    echo -e "${YELLOW}Coverage Report:${NC}"
    coverage report

    echo ""
    echo -e "${YELLOW}Generating HTML coverage report...${NC}"
    coverage html
    echo -e "${GREEN}HTML report generated in: htmlcov/index.html${NC}"

else
    echo -e "${YELLOW}Running tests...${NC}"
    echo ""

    python manage.py test "$TEST_PATH" \
        --verbosity=$VERBOSE \
        $KEEPDB \
        $PARALLEL
fi

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}  ✓ All tests passed!${NC}"
    echo -e "${GREEN}================================${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}================================${NC}"
    echo -e "${RED}  ✗ Some tests failed${NC}"
    echo -e "${RED}================================${NC}"
    exit 1
fi
