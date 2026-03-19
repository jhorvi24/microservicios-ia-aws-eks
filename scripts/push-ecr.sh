#!/bin/bash
set -e

echo "=== Build and Push Docker Images to ECR ==="

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "Project root: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# AWS Profile
AWS_PROFILE="aws-academy"

# Get AWS Account ID and Region
ACCOUNT_ID=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
REGION="us-east-1"
ECR_REGISTRY="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

echo "Account ID: $ACCOUNT_ID"
echo "ECR Registry: $ECR_REGISTRY"

# Login to ECR
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --profile $AWS_PROFILE --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Build and push each service
services=("nlp-service" "data-service" "dashboard")

for service in "${services[@]}"; do
  echo ""
  echo "=== Building $service ==="
  
  if [ ! -d "Services/$service" ]; then
    echo "  ✗ services/$service directory not found"
    exit 1
  fi
  
  cd Services/$service
  
  docker build -t $service:latest .
  docker tag $service:latest $ECR_REGISTRY/$service:latest
  
  echo "Pushing $service to ECR..."
  docker push $ECR_REGISTRY/$service:latest
  
  cd "$PROJECT_ROOT"
done

echo ""
echo "=== All images pushed successfully ==="
echo "You can now deploy to EKS: kubectl apply -f k8s/"