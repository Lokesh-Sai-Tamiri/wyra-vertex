#!/bin/bash

# Sales Intelligence API - Cloud Run Deployment Script
# Make sure to run: chmod +x deploy.sh

set -e

# Configuration
PROJECT_ID="wyra-477511"
SERVICE_NAME="sales-intelligence-api"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# API Key (set this or use --set-env-vars during deployment)
# Generate new key with: python3 -c "import secrets; print(secrets.token_urlsafe(32))"
API_KEY="${API_KEY:-x5ZK8PmzIFIZa79bMOaLHNuhgDf7-1HdJ4sUwSs9laA}"

echo "🚀 Deploying Sales Intelligence API to Cloud Run..."
echo "Project: ${PROJECT_ID}"
echo "Service: ${SERVICE_NAME}"
echo "Region: ${REGION}"
echo ""

# Set the active project
echo "📌 Setting active project..."
gcloud config set project ${PROJECT_ID}

# Build the container image
echo "🔨 Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 600 \
  --max-instances 10 \
  --min-instances 0 \
  --set-env-vars "PROJECT_ID=${PROJECT_ID},API_KEY=${API_KEY}"

# Get the service URL
echo ""
echo "✅ Deployment complete!"
echo ""
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --platform managed --region ${REGION} --format 'value(status.url)')
echo "🌐 Service URL: ${SERVICE_URL}"
echo ""
echo "📖 API Documentation: ${SERVICE_URL}/docs"
echo "❤️  Health Check: ${SERVICE_URL}/health"
echo ""
echo "🧪 Test the API with:"
echo "curl -X POST ${SERVICE_URL}/api/v1/analyze \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{"
echo "    \"company_name\": \"Futran Solutions\","
echo "    \"company_website\": \"https://futransolutions.com/\","
echo "    \"company_linkedin\": \"https://www.linkedin.com/company/futransolutionsinc/\""
echo "  }'"

