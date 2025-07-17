# Neptune Workbench Scheduler

Automatically start and stop an Amazon Neptune workbench (SageMaker notebook) on a defined schedule to optimize costs.

## Schedule

- **Weekdays**: Runs from 9 AM to 7 PM IST (3:30 AM to 1:30 PM UTC)
- **Weekends**: Stopped (Friday 7 PM to Monday 9 AM)

## Deployment Options

### CloudFormation

1. Log in to AWS Console
2. Navigate to CloudFormation
3. Create stack > With new resources
4. Upload `sagemaker-notebook-scheduler.yaml`
5. Enter stack name and review parameters
6. Create stack

### Terraform

1. Install Terraform
2. Create Lambda deployment package:
   ```bash
   zip lambda_function.zip lambda_function.py
   ```
3. Run Terraform commands:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

## Parameters

- `NotebookInstanceName`: Default is "aws-neptune-sample-ng"
- `StopScheduleExpression`: Default is 7 PM IST weekdays
- `StartScheduleExpression`: Default is 9 AM IST weekdays

## Cost

Minimal cost (approximately $0.05/month) after free tier expiration.
