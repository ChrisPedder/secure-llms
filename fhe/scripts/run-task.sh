#!/usr/bin/env bash
set -euo pipefail

STACK_NAME="SecureLlmsFhe"

echo "Fetching stack outputs..."
BUCKET=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text)
CLUSTER_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='ClusterArn'].OutputValue" --output text)
TASK_DEF_ARN=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='TaskDefinitionArn'].OutputValue" --output text)
SUBNETS=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='PrivateSubnets'].OutputValue" --output text)
LOG_GROUP=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='LogGroupName'].OutputValue" --output text)

echo "Bucket:   $BUCKET"
echo "Cluster:  $CLUSTER_ARN"
echo "Task Def: $TASK_DEF_ARN"
echo "Subnets:  $SUBNETS"
echo "Logs:     $LOG_GROUP"
echo ""

DATA_FILE="${1:-./data/creditcard.csv}"
echo "Uploading dataset from $DATA_FILE to s3://$BUCKET/creditcard.csv..."
aws s3 cp "$DATA_FILE" "s3://$BUCKET/creditcard.csv"
echo ""

echo "Starting Fargate task..."
TASK_ARN=$(aws ecs run-task \
  --cluster "$CLUSTER_ARN" \
  --task-definition "$TASK_DEF_ARN" \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[${SUBNETS}],assignPublicIp=DISABLED}" \
  --query "tasks[0].taskArn" --output text)

echo "Task started: $TASK_ARN"
TASK_ID=$(echo "$TASK_ARN" | awk -F/ '{print $NF}')
echo "Streaming logs from $LOG_GROUP/fhe/$TASK_ID ..."
echo "(Ctrl+C to stop streaming — the task will continue running)"
echo ""

sleep 10

aws logs tail "$LOG_GROUP" --follow --format short \
  --log-stream-name-prefix "fhe/$TASK_ID" 2>/dev/null || \
  echo "Log streaming ended. Check CloudWatch for full output: $LOG_GROUP"
