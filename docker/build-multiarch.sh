#!/bin/bash

# Multi-architecture Docker build script
# Supports: linux/amd64 (x86_64) and linux/arm64 (ARM)

set -e

echo "=========================================="
echo "  Multi-Architecture Docker Build"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if buildx is available
if ! docker buildx version &> /dev/null; then
    echo -e "${RED}Error: docker buildx not found${NC}"
    echo "Please upgrade to Docker 19.03+ with buildx support"
    exit 1
fi

# Detect current platform
CURRENT_ARCH=$(uname -m)
case $CURRENT_ARCH in
    x86_64)
        CURRENT_PLATFORM="linux/amd64"
        ;;
    arm64|aarch64)
        CURRENT_PLATFORM="linux/arm64"
        ;;
    *)
        echo -e "${RED}Unknown architecture: $CURRENT_ARCH${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}Current platform: $CURRENT_PLATFORM${NC}"
echo ""

# Menu
echo "Select build option:"
echo "  1) Build for current platform only ($CURRENT_PLATFORM)"
echo "  2) Build for AMD64 (linux/amd64)"
echo "  3) Build for ARM64 (linux/arm64)"
echo "  4) Build for both AMD64 and ARM64"
echo "  0) Exit"
echo ""
read -p "Choose (0-4): " choice

case $choice in
    1)
        PLATFORMS=$CURRENT_PLATFORM
        ;;
    2)
        PLATFORMS="linux/amd64"
        ;;
    3)
        PLATFORMS="linux/arm64"
        ;;
    4)
        PLATFORMS="linux/amd64,linux/arm64"
        ;;
    0)
        echo "Cancelled"
        exit 0
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Building for: $PLATFORMS${NC}"
echo ""

# Create buildx builder if not exists
BUILDER_NAME="news2context-builder"
if ! docker buildx inspect $BUILDER_NAME &> /dev/null; then
    echo "Creating buildx builder..."
    docker buildx create --name $BUILDER_NAME --use
else
    echo "Using existing builder: $BUILDER_NAME"
    docker buildx use $BUILDER_NAME
fi

# Build images
echo ""
echo "Building backend..."
docker buildx build \
    --platform $PLATFORMS \
    -f docker/Dockerfile.backend \
    -t news2context-backend:latest \
    --load \
    .

echo ""
echo "Building scheduler..."
docker buildx build \
    --platform $PLATFORMS \
    -f docker/Dockerfile.scheduler \
    -t news2context-scheduler:latest \
    --load \
    .

echo ""
echo "Building frontend..."
docker buildx build \
    --platform $PLATFORMS \
    -f docker/Dockerfile.frontend \
    -t news2context-frontend:latest \
    --load \
    .

echo ""
echo -e "${GREEN}✓ Build complete!${NC}"
echo ""
echo "Images built:"
docker images | grep news2context

echo ""
echo "To start services:"
echo "  docker-compose up -d"
