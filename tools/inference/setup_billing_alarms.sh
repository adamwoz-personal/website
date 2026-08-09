#!/usr/bin/env bash
# Set up CloudWatch billing alarms for the wosotowsky.org stack.
#
# Run this from a workstation (or Cloud Shell) with admin AWS credentials,
# NOT from the EC2 instance. The instance's IAM role is locked to Bedrock
# invoke only, which is the intended posture.
#
# Prereqs (one-time, root account only, in the console):
#   Billing preferences -> Alert preferences -> "Receive AWS Free Tier alerts"
#   AND "Receive CloudWatch billing alerts" both enabled.
#   Billing metrics are ONLY published in us-east-1.

set -euo pipefail

REGION=us-east-1
: "${EMAIL:?Set EMAIL to the address that should receive billing alarms}"
BEDROCK_THRESHOLD_USD=${BEDROCK_THRESHOLD_USD:-5}
TOTAL_THRESHOLD_USD=${TOTAL_THRESHOLD_USD:-25}

echo "Creating SNS topic..."
TOPIC_ARN=$(aws sns create-topic --name wosotowsky-billing-alerts --region "$REGION" --query TopicArn --output text)
echo "Topic: $TOPIC_ARN"

echo "Subscribing $EMAIL (confirmation email will arrive; click the link)..."
aws sns subscribe \
  --topic-arn "$TOPIC_ARN" \
  --protocol email \
  --notification-endpoint "$EMAIL" \
  --region "$REGION" >/dev/null

echo "Creating Bedrock alarm at \$$BEDROCK_THRESHOLD_USD..."
aws cloudwatch put-metric-alarm --region "$REGION" \
  --alarm-name "wosotowsky-bedrock-monthly-usd" \
  --alarm-description "Estimated AWS Bedrock charges exceed \$$BEDROCK_THRESHOLD_USD for the current month" \
  --namespace "AWS/Billing" \
  --metric-name "EstimatedCharges" \
  --dimensions Name=ServiceName,Value=AmazonBedrock Name=Currency,Value=USD \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold "$BEDROCK_THRESHOLD_USD" \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions "$TOPIC_ARN"

echo "Creating total-account alarm at \$$TOTAL_THRESHOLD_USD..."
aws cloudwatch put-metric-alarm --region "$REGION" \
  --alarm-name "wosotowsky-total-monthly-usd" \
  --alarm-description "Estimated total AWS charges exceed \$$TOTAL_THRESHOLD_USD for the current month" \
  --namespace "AWS/Billing" \
  --metric-name "EstimatedCharges" \
  --dimensions Name=Currency,Value=USD \
  --statistic Maximum \
  --period 21600 \
  --evaluation-periods 1 \
  --threshold "$TOTAL_THRESHOLD_USD" \
  --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions "$TOPIC_ARN"

echo
echo "Done. Confirm the SNS subscription in your email inbox."
aws cloudwatch describe-alarms --region "$REGION" \
  --alarm-name-prefix wosotowsky \
  --query 'MetricAlarms[*].[AlarmName,StateValue,Threshold]' \
  --output table
