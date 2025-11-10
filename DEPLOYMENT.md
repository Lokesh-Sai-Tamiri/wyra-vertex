# 🚀 Cloud Run Deployment Guide

## Prerequisites

1. **Google Cloud CLI installed**
   ```bash
   # Install if not already installed
   # Mac: brew install google-cloud-sdk
   # Or visit: https://cloud.google.com/sdk/docs/install
   ```

2. **Authenticate with Google Cloud**
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. **Enable required APIs**
   ```bash
   gcloud services enable cloudbuild.googleapis.com
   gcloud services enable run.googleapis.com
   gcloud services enable aiplatform.googleapis.com
   ```

## 🎯 Quick Deploy (Recommended)

### Option 1: Using the Deployment Script

```bash
# Make the script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### Option 2: Manual Deployment

```bash
# Set your project
gcloud config set project wyra-477511

# Build the container
gcloud builds submit --tag gcr.io/wyra-477511/sales-intelligence-api

# Deploy to Cloud Run
gcloud run deploy sales-intelligence-api \
  --image gcr.io/wyra-477511/sales-intelligence-api \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 1 \
  --timeout 600 \
  --max-instances 10
```

## 🧪 Testing Your Deployment

### 1. Health Check
```bash
curl https://YOUR-SERVICE-URL.run.app/health
```

### 2. API Documentation
Visit: `https://YOUR-SERVICE-URL.run.app/docs`

### 3. Test Analysis Endpoint
```bash
curl -X POST https://YOUR-SERVICE-URL.run.app/api/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Futran Solutions",
    "company_website": "https://futransolutions.com/",
    "company_linkedin": "https://www.linkedin.com/company/futransolutionsinc/"
  }'
```

## 🔧 Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --port 8080
```

Then visit:
- API: http://localhost:8080
- Docs: http://localhost:8080/docs
- Health: http://localhost:8080/health

## 📊 Monitoring & Logs

### View Logs
```bash
gcloud run services logs read sales-intelligence-api \
  --region us-central1 \
  --limit 50
```

### Stream Logs (Real-time)
```bash
gcloud run services logs tail sales-intelligence-api \
  --region us-central1
```

### View Metrics in Console
```bash
# Open in browser
gcloud run services describe sales-intelligence-api \
  --region us-central1 \
  --format="value(status.url)"
```

Then go to: Cloud Console → Cloud Run → Select your service → Metrics

## 🔐 Security Configuration

### Option 1: Require Authentication
```bash
gcloud run deploy sales-intelligence-api \
  --image gcr.io/wyra-477511/sales-intelligence-api \
  --no-allow-unauthenticated
```

Then call with auth:
```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://YOUR-SERVICE-URL.run.app/api/v1/analyze
```

### Option 2: Use Workload Identity (Recommended for Production)

Instead of copying service-account.json, use Workload Identity:

```bash
# Create service account
gcloud iam service-accounts create sales-intelligence-sa \
  --display-name="Sales Intelligence Service Account"

# Grant Vertex AI access
gcloud projects add-iam-policy-binding wyra-477511 \
  --member="serviceAccount:sales-intelligence-sa@wyra-477511.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# Deploy with service account
gcloud run deploy sales-intelligence-api \
  --image gcr.io/wyra-477511/sales-intelligence-api \
  --service-account=sales-intelligence-sa@wyra-477511.iam.gserviceaccount.com
```

## ⚙️ Configuration Options

### Environment Variables
```bash
gcloud run services update sales-intelligence-api \
  --set-env-vars "PROJECT_ID=wyra-477511,LOG_LEVEL=INFO"
```

### Resource Limits
```bash
# Increase memory for larger requests
gcloud run services update sales-intelligence-api \
  --memory 4Gi \
  --cpu 2

# Adjust timeout (max 3600s)
gcloud run services update sales-intelligence-api \
  --timeout 900
```

### Auto-scaling
```bash
gcloud run services update sales-intelligence-api \
  --min-instances 1 \
  --max-instances 20
```

## 🐛 Troubleshooting

### Build Fails
```bash
# Check build logs
gcloud builds list --limit 5
gcloud builds log BUILD_ID
```

### Service Won't Start
```bash
# Check service status
gcloud run services describe sales-intelligence-api --region us-central1

# Check recent logs
gcloud run services logs read sales-intelligence-api --limit 100
```

### Vertex AI Permission Errors
```bash
# Verify service account has correct permissions
gcloud projects get-iam-policy wyra-477511 \
  --flatten="bindings[].members" \
  --filter="bindings.members:sales-intelligence-sa@wyra-477511.iam.gserviceaccount.com"
```

## 💰 Cost Optimization

1. **Set min-instances to 0** (default) for development
2. **Use --concurrency 80** to handle more requests per instance
3. **Set appropriate timeout** (don't use max if not needed)
4. **Monitor usage** in Cloud Console

## 🔄 CI/CD Integration

### GitHub Actions Example
Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - id: 'auth'
      uses: 'google-github-actions/auth@v1'
      with:
        credentials_json: '${{ secrets.GCP_SA_KEY }}'
    
    - name: Deploy to Cloud Run
      run: |
        gcloud builds submit --tag gcr.io/wyra-477511/sales-intelligence-api
        gcloud run deploy sales-intelligence-api \
          --image gcr.io/wyra-477511/sales-intelligence-api \
          --region us-central1 \
          --platform managed
```

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint with service info |
| `/health` | GET | Health check for monitoring |
| `/docs` | GET | Interactive API documentation (Swagger) |
| `/api/v1/analyze` | POST | Generate sales intelligence report |

## 🎓 Next Steps

1. ✅ Deploy to staging environment first
2. ✅ Test with sample companies
3. ✅ Set up monitoring alerts
4. ✅ Configure authentication if needed
5. ✅ Set up CI/CD pipeline
6. ✅ Monitor costs and optimize

## 📞 Support

For issues or questions:
- Check Cloud Run logs
- Review Vertex AI quotas
- Verify IAM permissions
- Check billing is enabled

