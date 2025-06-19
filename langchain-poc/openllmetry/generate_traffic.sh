#!/bin/bash

# Configuration
SERVER_URL="http://localhost:8000"
DELAY_SECONDS=10  # Increased to avoid AWS Bedrock throttling
NUM_REQUESTS=0  # 0 for infinite
TIMEOUT=30

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Sample messages array
MESSAGES=(
    "What is artificial intelligence?"
    "Explain the concept of neural networks"
    "How does natural language processing work?"
    "What are the applications of machine learning?"
    "Describe the difference between supervised and unsupervised learning"
    "What is deep learning?"
    "How do recommendation systems work?"
    "Explain computer vision in simple terms"
    "What are the ethical considerations in AI?"
    "How does reinforcement learning work?"
    "What is transfer learning?"
    "Explain the concept of bias in AI"
    "What are transformer models?"
    "How does sentiment analysis work?"
    "What is edge computing in AI?"
)

# Function to send a request
send_request() {
    local message="${MESSAGES[$RANDOM % ${#MESSAGES[@]}]}"
    local start_time=$(date +%s)
    
    # Send request and capture response
    response=$(curl -s -w "\n%{http_code}" -X POST "$SERVER_URL/chat" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"$message\"}" \
        --max-time $TIMEOUT)
    
    # Extract status code and response body
    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n-1)
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    if [ "$status_code" = "200" ]; then
        echo -e "${GREEN}✓${NC} Request $1 successful (${duration}s)"
        echo "   Message: $message"
        echo "   Response preview: $(echo "$response_body" | jq -r '.response' 2>/dev/null | head -c 100)..."
    else
        echo -e "${RED}✗${NC} Request $1 failed with status $status_code"
        echo "   Message: $message"
        echo "   Error: $response_body"
    fi
}

# Function to check server health
check_health() {
    echo "Checking server health..."
    health_response=$(curl -s -w "\n%{http_code}" "$SERVER_URL/health" --max-time 5)
    health_status=$(echo "$health_response" | tail -n1)
    
    if [ "$health_status" = "200" ]; then
        echo -e "${GREEN}✓${NC} Server is healthy"
        return 0
    else
        echo -e "${RED}✗${NC} Server health check failed"
        return 1
    fi
}

# Trap Ctrl+C to exit gracefully
trap 'echo -e "\n${YELLOW}Traffic generation stopped by user${NC}"; exit 0' INT

# Main execution
echo "==================================="
echo "OpenLLMetry Traffic Generator"
echo "==================================="
echo "Server URL: $SERVER_URL"
echo "Delay between requests: ${DELAY_SECONDS}s"
echo "Number of requests: $([ $NUM_REQUESTS -eq 0 ] && echo "∞" || echo $NUM_REQUESTS)"
echo "==================================="

# Check server health before starting
if ! check_health; then
    echo -e "${RED}Server is not responding. Please ensure the server is running.${NC}"
    echo "Start the server with: python server.py"
    exit 1
fi

echo -e "\nStarting traffic generation...\n"

# Request counter
count=0
success_count=0
fail_count=0

# Main loop
while [ $NUM_REQUESTS -eq 0 ] || [ $count -lt $NUM_REQUESTS ]; do
    count=$((count + 1))
    
    send_request $count
    
    # Update counters based on last status
    if [ "$status_code" = "200" ]; then
        success_count=$((success_count + 1))
    else
        fail_count=$((fail_count + 1))
    fi
    
    # Show progress every 10 requests
    if [ $((count % 10)) -eq 0 ]; then
        echo -e "\n${YELLOW}Progress: $count requests sent (Success: $success_count, Failed: $fail_count)${NC}\n"
    fi
    
    # Wait before next request (except for the last one)
    if [ $NUM_REQUESTS -eq 0 ] || [ $count -lt $NUM_REQUESTS ]; then
        sleep $DELAY_SECONDS
    fi
done

# Final summary
echo -e "\n==================================="
echo -e "${YELLOW}Traffic generation completed!${NC}"
echo -e "Total requests: $count"
echo -e "${GREEN}Successful: $success_count${NC}"
echo -e "${RED}Failed: $fail_count${NC}"
echo "===================================" 