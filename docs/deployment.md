# Deployment Guide: Cloud Run

## Prerequisites
- GCP project with billing enabled
- gcloud CLI authenticated
- Docker installed (for local testing)

## Step 1: Enable APIs
```bash
gcloud services enable run.googleapis.com aiplatform.googleapis.com
```

## Step 2: Build Container
```bash
cd /root/projects/gc-rapid-agent
gcloud builds submit --tag gcr.io/$PROJECT_ID/agentic-auditor:v1
```

## Step 3: Deploy to Cloud Run
```bash
gcloud run deploy agentic-auditor \
  --image gcr.io/$PROJECT_ID/agentic-auditor:v1 \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="PROJECT_ID=$PROJECT_ID,REGION=us-central1"
```

## Step 4: Verify
```bash
curl -X POST $(gcloud run services describe agentic-auditor --format='value(status.url)') \
  -H "Content-Type: application/json" \
  -d '{"contract_code": "function test() { selfdestruct(msg.sender); }"}'
```

## Environment Variables
| Variable | Required | Description |
|----------|----------|-------------|
| `PROJECT_ID` | Yes | GCP project ID |
| `REGION` | Yes | GCP region |
| `BUCKET_NAME` | Yes | Cloud Storage bucket for reports |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | Service account key path |
| `ETHERSCAN_API_KEY` | No | For fetching deployed contracts |
| `RPC_URL_BASE` | No | Base network RPC |
| `SLITHER_PATH` | No | Path to Slither binary |

## Troubleshooting
- **Permission denied**: Ensure service account has `roles/run.invoker`
- **Model not found**: Enable `aiplatform.googleapis.com` API
- **Timeout**: Increase Cloud Run timeout to 300s for long analyses
