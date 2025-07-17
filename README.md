# SageMaker Notebook Scheduler

CloudFormation template to automatically start and stop a SageMaker notebook instance on a defined schedule.

## Schedule

- **Weekdays**: Runs from 9 AM to 7 PM IST (3:30 AM to 1:30 PM UTC)
- **Weekends**: Stopped (Friday 7 PM to Monday 9 AM)

## Resources Created

- Lambda functions for starting and stopping the notebook
- EventBridge rules for scheduling
- IAM role with required permissions

## Deployment

1. Log in to AWS Console
2. Navigate to CloudFormation
3. Create stack > With new resources
4. Upload `sagemaker-notebook-scheduler.yaml`
5. Enter stack name and review parameters
6. Create stack

## Parameters

- `NotebookInstanceName`: Default is "aws-neptune-sample-ng"
- `StopScheduleExpression`: Default is 7 PM IST weekdays
- `StartScheduleExpression`: Default is 9 AM IST weekdays

## Cost

Minimal cost (approximately $0.05/month) after free tier expiration.
