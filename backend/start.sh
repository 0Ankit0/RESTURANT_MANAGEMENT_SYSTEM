#!/bin/bash
# Quick start script for running the application with Celery

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if .env exists
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
fi

# Check DEBUG setting
DEBUG=$(grep "^DEBUG=" .env | cut -d'=' -f2)
PROJECT_NAME=$(grep "^PROJECT_NAME=" .env | cut -d'=' -f2-)

if [ -z "$PROJECT_NAME" ]; then
    PROJECT_NAME="Project Template"
fi

echo -e "${BLUE}Starting ${PROJECT_NAME} with Celery${NC}"
echo ""

if [ "$DEBUG" = "False" ]; then
    echo -e "${BLUE}Production mode detected. Checking Redis...${NC}"
    
    # Check if Redis is running
    if command -v redis-cli &> /dev/null; then
        if redis-cli ping &> /dev/null; then
            echo -e "${GREEN}✓ Redis is running${NC}"
        else
            echo "⚠️  Redis is not running. Starting Redis..."
            echo "Please start Redis manually:"
            echo "  macOS: brew services start redis"
            echo "  Linux: sudo systemctl start redis-server"
            echo "  Docker: docker run -d -p 6379:6379 redis:alpine"
            exit 1
        fi
    else
        echo "⚠️  Redis not found. Please install Redis for production mode."
        echo "  macOS: brew install redis"
        echo "  Linux: sudo apt-get install redis-server"
        exit 1
    fi
else
    echo -e "${GREEN}✓ Development mode - using in-memory broker${NC}"
fi

echo ""
echo "To run the application:"
echo ""
echo "Terminal 1 - Start Celery Worker:"
echo "  task celery"
echo ""
echo "Terminal 2 - Start FastAPI Server:"
echo "  task start"
echo ""
