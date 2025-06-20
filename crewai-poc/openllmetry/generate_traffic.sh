#!/bin/bash

# CrewAI OpenLLMetry Traffic Generator
# This script sends requests to the CrewAI server to generate trace data

# Configuration
SERVER_URL="${SERVER_URL:-http://localhost:8000}"
DELAY_SECONDS="${DELAY_SECONDS:-60}"    # Default: 1 minute between requests
MAX_REQUESTS="${MAX_REQUESTS:-0}"       # 0 = infinite loop

# Color codes for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Sample queries
QUERIES=(
    "What are the best practices for implementing observability in microservices architectures?"
    "Explain the differences between monitoring, logging, and tracing in distributed systems"
    "How can OpenTelemetry help improve application performance monitoring?"
    "What are the key metrics to track in a cloud-native application?"
    "Describe the benefits of distributed tracing for debugging complex systems"
    "How do you implement effective alerting strategies for production systems?"
    "What are the common challenges in implementing observability at scale?"
    "Explain the concept of Service Level Objectives (SLOs) and their importance"
    "How can machine learning enhance observability and anomaly detection?"
    "What are the best practices for log aggregation and analysis in distributed systems?"
)

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if server is running
check_server() {
    print_status "Checking server health..."
    if curl -s "${SERVER_URL}/health" > /dev/null; then
        print_success "Server is healthy"
        return 0
    else
        print_error "Server is not responding at ${SERVER_URL}"
        return 1
    fi
}

# Function to send a chat request
send_chat_request() {
    local query="$1"
    print_status "Sending chat request: \"${query}\""
    
    response=$(curl -s -X POST "${SERVER_URL}/chat" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"${query}\"}" \
        -w "\n%{http_code}")
    
    http_code=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        print_success "Chat request completed successfully"
        echo -e "${GREEN}Response preview:${NC} $(echo "$body" | jq -r '.response' | head -c 100)..."
    else
        print_error "Chat request failed with HTTP code: $http_code"
    fi
}

# Function to send a batch request
send_batch_request() {
    print_status "Sending batch request with 3 queries..."
    
    # Select 3 random queries
    local batch_queries=()
    for i in {1..3}; do
        batch_queries+=("${QUERIES[$RANDOM % ${#QUERIES[@]}]}")
    done
    
    # Create JSON array
    local json_array=$(printf '%s\n' "${batch_queries[@]}" | jq -R . | jq -s .)
    
    response=$(curl -s -X POST "${SERVER_URL}/batch" \
        -H "Content-Type: application/json" \
        -d "{\"messages\": ${json_array}}" \
        -w "\n%{http_code}")
    
    http_code=$(echo "$response" | tail -n 1)
    
    if [ "$http_code" = "200" ]; then
        print_success "Batch request completed successfully"
    else
        print_error "Batch request failed with HTTP code: $http_code"
    fi
}

# Function to send a sample request
send_sample_request() {
    print_status "Sending sample request..."
    
    response=$(curl -s "${SERVER_URL}/sample" -w "\n%{http_code}")
    http_code=$(echo "$response" | tail -n 1)
    
    if [ "$http_code" = "200" ]; then
        print_success "Sample request completed successfully"
    else
        print_error "Sample request failed with HTTP code: $http_code"
    fi
}

# Main execution
main() {
    echo -e "${BLUE}=== CrewAI OpenLLMetry Traffic Generator ===${NC}"
    echo "Server URL: ${SERVER_URL}"
    echo "Delay between requests: ${DELAY_SECONDS} seconds"
    echo "Max requests: ${MAX_REQUESTS} (0 = infinite)"
    echo ""
    
    # Check if jq is installed
    if ! command -v jq &> /dev/null; then
        print_warning "jq is not installed. Install it for better output formatting."
    fi
    
    # Initial server check
    if ! check_server; then
        print_error "Please ensure the CrewAI server is running at ${SERVER_URL}"
        exit 1
    fi
    
    request_count=0
    
    # Main loop
    while true; do
        request_count=$((request_count + 1))
        
        echo ""
        print_status "Starting request cycle #${request_count}"
        
        # Randomly select request type
        request_type=$((RANDOM % 3))
        
        case $request_type in
            0)
                # Send chat request with random query
                query="${QUERIES[$RANDOM % ${#QUERIES[@]}]}"
                send_chat_request "$query"
                ;;
            1)
                # Send batch request
                send_batch_request
                ;;
            2)
                # Send sample request
                send_sample_request
                ;;
        esac
        
        # Check if we've reached max requests
        if [ "$MAX_REQUESTS" -gt 0 ] && [ "$request_count" -ge "$MAX_REQUESTS" ]; then
            print_status "Reached maximum number of requests (${MAX_REQUESTS})"
            break
        fi
        
        # Wait before next request
        print_status "Waiting ${DELAY_SECONDS} seconds before next request..."
        print_status "Press Ctrl+C to stop"
        sleep "$DELAY_SECONDS"
    done
    
    echo ""
    print_status "Traffic generation completed. Total requests: ${request_count}"
}

# Trap Ctrl+C to exit gracefully
trap 'echo ""; print_warning "Interrupted by user"; exit 0' INT

# Run main function
main