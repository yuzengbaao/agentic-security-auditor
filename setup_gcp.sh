#!/bin/bash
# =============================================================================
# GCP Environment Setup Script for Agentic Security Auditor
# Google Cloud Rapid Agent Hackathon 2026
# =============================================================================
# Usage:
#   chmod +x setup_gcp.sh
#   ./setup_gcp.sh <PROJECT_ID> <REGION>
#
# Prerequisites:
#   - gcloud CLI installed
#   - Google account with billing enabled
# =============================================================================

set -e

PROJECT_ID="${1:-agentic-auditor-hackathon}"
REGION="${2:-us-central1}"

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  GCP Environment Setup: Agentic Security Auditor               ║"
echo "║  Project: $PROJECT_ID                                          ║"
echo "║  Region:  $REGION                                               ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# ── Step 1: Check gcloud ──
echo "[1/8] Verifying gcloud CLI..."
gcloud --version | head -1

# ── Step 2: Authenticate (if not already) ──
echo ""
echo "[2/8] Checking GCP authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo "  → No active account found. Initiating login..."
    gcloud auth login
fi
ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
echo "  ✓ Active account: $ACTIVE_ACCOUNT"

# ── Step 3: Create/Set GCP Project ──
echo ""
echo "[3/8] Setting up GCP project: $PROJECT_ID"
if gcloud projects list --format="value(projectId)" | grep -q "^${PROJECT_ID}$"; then
    echo "  ✓ Project exists"
else
    echo "  → Creating new project..."
    gcloud projects create "$PROJECT_ID" --name="Agentic Security Auditor"
    echo "  ⚠ Please enable billing at: https://console.cloud.google.com/billing"
    read -p "  Press Enter after billing is enabled..."
fi
gcloud config set project "$PROJECT_ID"

# ── Step 4: Enable Required APIs ──
echo ""
echo "[4/8] Enabling required APIs..."
APIS=(
    "aiplatform.googleapis.com"          # Vertex AI
    "agentbuilder.googleapis.com"         # Agent Builder
    "run.googleapis.com"                  # Cloud Run
    "storage.googleapis.com"              # Cloud Storage
    "secretmanager.googleapis.com"        # Secret Manager
    "cloudbuild.googleapis.com"           # Cloud Build
    "artifactregistry.googleapis.com"     # Artifact Registry
)

for api in "${APIS[@]}"; do
    echo "  → Enabling $api"
    gcloud services enable "$api" --project="$PROJECT_ID"
done
echo "  ✓ All APIs enabled"

# ── Step 5: Create Service Account ──
echo ""
echo "[5/8] Creating service account..."
SA_NAME="agentic-auditor-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts list --project="$PROJECT_ID" --format="value(email)" | grep -q "$SA_EMAIL"; then
    echo "  ✓ Service account exists: $SA_EMAIL"
else
    gcloud iam service-accounts create "$SA_NAME" \
        --display-name="Agentic Security Auditor Service Account" \
        --project="$PROJECT_ID"
    echo "  ✓ Created: $SA_EMAIL"
fi

# Grant roles
echo "  → Granting IAM roles..."
gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/aiplatform.user" --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.invoker" --quiet

gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectAdmin" --quiet

echo "  ✓ Roles granted"

# ── Step 6: Create Cloud Storage Bucket ──
echo ""
echo "[6/8] Creating Cloud Storage bucket..."
BUCKET_NAME="${PROJECT_ID}-reports"
if gsutil ls -b "gs://$BUCKET_NAME" 2>/dev/null | grep -q "$BUCKET_NAME"; then
    echo "  ✓ Bucket exists: gs://$BUCKET_NAME"
else
    gsutil mb -l "$REGION" "gs://$BUCKET_NAME"
    echo "  ✓ Created: gs://$BUCKET_NAME"
fi

# ── Step 7: Set Default Region ──
echo ""
echo "[7/8] Setting default region..."
gcloud config set run/region "$REGION"
gcloud config set ai/region "$REGION"
echo "  ✓ Region set to: $REGION"

# ── Step 8: Verify ──
echo ""
echo "[8/8] Verification..."
echo "  Project: $(gcloud config get-value project)"
echo "  Region:  $(gcloud config get-value run/region)"
echo "  Account: $(gcloud auth list --filter=status:ACTIVE --format='value(account)' | head -1)"
echo ""

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║  ✅ GCP Environment Ready!                                         ║"
echo "╠════════════════════════════════════════════════════════════════════╣"
echo "║  Next steps:                                                       ║"
echo "║  1. Ensure billing is enabled for $PROJECT_ID                     ║"
echo "║  2. Download service account key:                                  ║"
echo "║     gcloud iam service-accounts keys create key.json               ║"
echo "║       --iam-account=$SA_EMAIL                                      ║"
echo "║  3. Set env: export GOOGLE_APPLICATION_CREDENTIALS=./key.json     ║"
echo "║  4. Test: gcloud ai models list                                    ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
