#!/bin/bash
# ─────────────────────────────────────────────────────────────
# connect-rds.sh
# Connects to RDS via SSM Session Manager port forwarding
# Usage: ./connect-rds.sh
# ─────────────────────────────────────────────────────────────

set -e

# ── Config ────────────────────────────────────────────────────
AWS_REGION="us-east-1"
BASTION_TAG="cloudtasks-bastion"
LOCAL_PORT="5432"
RDS_PORT="5432"

# ── Colors ────────────────────────────────────────────────────
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🔌 Connecting to RDS via SSM...${NC}"

# ── Check dependencies ────────────────────────────────────────
echo "Checking dependencies..."

if ! command -v aws &> /dev/null; then
  echo -e "${RED}❌ AWS CLI not installed. Run: brew install awscli${NC}"
  exit 1
fi

if ! command -v session-manager-plugin &> /dev/null; then
  echo -e "${RED}❌ SSM plugin not installed.${NC}"
  echo "Mac:   brew install --cask session-manager-plugin"
  echo "Linux: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html"
  exit 1
fi

if ! command -v psql &> /dev/null; then
  echo -e "${RED}❌ psql not installed.${NC}"
  echo "Mac:   brew install postgresql"
  echo "Linux: sudo apt install postgresql-client"
  exit 1
fi

# ── Get bastion instance ID ───────────────────────────────────
echo "Finding bastion instance..."

INSTANCE_ID=$(aws ec2 describe-instances \
  --region "$AWS_REGION" \
  --filters \
    "Name=tag:Name,Values=${BASTION_TAG}" \
    "Name=instance-state-name,Values=running" \
  --query "Reservations[0].Instances[0].InstanceId" \
  --output text)

if [ "$INSTANCE_ID" == "None" ] || [ -z "$INSTANCE_ID" ]; then
  echo -e "${RED}❌ Bastion instance not found. Is Terraform Apply done?${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Found bastion: $INSTANCE_ID${NC}"

# ── Get RDS endpoint ──────────────────────────────────────────
echo "Getting RDS endpoint..."

RDS_ENDPOINT=$(aws rds describe-db-instances \
  --region "$AWS_REGION" \
  --query "DBInstances[?contains(DBInstanceIdentifier, 'cloudtasks')].Endpoint.Address" \
  --output text)

if [ -z "$RDS_ENDPOINT" ]; then
  echo -e "${RED}❌ RDS endpoint not found. Is Terraform Apply done?${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Found RDS: $RDS_ENDPOINT${NC}"

# ── Load credentials from .env ────────────────────────────────
if [ ! -f ".env" ]; then
  echo -e "${RED}❌ .env file not found in current directory${NC}"
  exit 1
fi

echo "Loading credentials from .env..."
export $(grep -v '^#' .env | xargs)

DB_USER=${POSTGRES_USER}
DB_PASSWORD=${POSTGRES_PASSWORD}
DB_NAME=${POSTGRES_DB:-taskdb}

if [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
  echo -e "${RED}❌ POSTGRES_USER or POSTGRES_PASSWORD missing from .env${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Credentials loaded${NC}"

# ── Start SSM port forwarding in background ───────────────────
echo -e "${YELLOW}Starting SSM tunnel on localhost:${LOCAL_PORT}...${NC}"

aws ssm start-session \
  --region "$AWS_REGION" \
  --target "$INSTANCE_ID" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{
    \"host\": [\"${RDS_ENDPOINT}\"],
    \"portNumber\": [\"${RDS_PORT}\"],
    \"localPortNumber\": [\"${LOCAL_PORT}\"]
  }" &

SSM_PID=$!

# ── Wait for tunnel to be ready ───────────────────────────────
echo "Waiting for tunnel..."
sleep 10

# ── Connect to RDS ────────────────────────────────────────────
echo -e "${GREEN}✅ Tunnel ready — connecting to RDS...${NC}"
echo -e "${YELLOW}Type \\q to exit psql and close the tunnel${NC}"
echo ""

PGPASSWORD="$DB_PASSWORD" psql \
  -h 127.0.0.1 \
  -p "$LOCAL_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME"

# ── Cleanup ───────────────────────────────────────────────────
echo ""
echo "Closing SSM tunnel..."
kill $SSM_PID 2>/dev/null
echo -e "${GREEN}✅ Done — tunnel closed${NC}"
