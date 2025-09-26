#!/bin/bash

# Deployment automation script for Universal Logging Hook Microservice
# Builds Docker image, pushes to registry, deploys to Kubernetes (basic).
# For production; customize with your registry and K8s context.

set -e

# Build Docker image
echo "Building Docker image..."
docker build -t your-repo/logging-microservice:latest .

# Push to registry (replace with your registry)
echo "Pushing image to registry..."
docker push your-repo/logging-microservice:latest

# Deploy to Kubernetes (assumes kubectl configured)
echo "Deploying to Kubernetes..."
kubectl apply -f k8s/deployment.yaml  # Assuming k8s/ folder with manifests
kubectl apply -f k8s/service.yaml     # Add if you have a service manifest

# Optional: Rollout status
kubectl rollout status deployment/logging-api

echo "Deployment complete! Check pods with 'kubectl get pods'"