provider "aws" {
  region = "us-east-1"  # Change to your region
}

variable "notebook_name" {
  description = "Name of the Neptune workbench notebook instance"
  default     = "aws-neptune-sample-ng"
}

variable "stop_schedule" {
  description = "Cron expression for stopping the notebook (7 PM IST / 1:30 PM UTC, Mon-Fri)"
  default     = "cron(30 13 ? * MON-FRI *)"
}

variable "start_schedule" {
  description = "Cron expression for starting the notebook (9 AM IST / 3:30 AM UTC, Mon-Fri)"
  default     = "cron(30 3 ? * MON-FRI *)"
}

# IAM Role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "neptune_workbench_scheduler_role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })
}

# IAM Policy for Lambda
resource "aws_iam_policy" "lambda_policy" {
  name        = "neptune_workbench_scheduler_policy"
  description = "Policy for Neptune workbench scheduler Lambda"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "arn:aws:logs:*:*:*"
    },
    {
      Effect = "Allow"
      Action = [
        "sagemaker:StopNotebookInstance",
        "sagemaker:StartNotebookInstance",
        "sagemaker:DescribeNotebookInstance"
      ]
      Resource = "arn:aws:sagemaker:*:*:notebook-instance/${var.notebook_name}"
    }]
  })
}

# Attach policy to role
resource "aws_iam_role_policy_attachment" "lambda_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.lambda_policy.arn
}

# Lambda function to stop notebook
resource "aws_lambda_function" "stop_notebook" {
  function_name    = "neptune_workbench_stop"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  
  environment {
    variables = {
      NOTEBOOK_NAME = var.notebook_name
      ACTION        = "stop"
    }
  }
  
  filename         = "lambda_function.zip"
  source_code_hash = filebase64sha256("lambda_function.zip")
  
  # Inline Lambda code
  # Note: For production, use a proper deployment package
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

# Lambda function to start notebook
resource "aws_lambda_function" "start_notebook" {
  function_name    = "neptune_workbench_start"
  role             = aws_iam_role.lambda_role.arn
  handler          = "index.lambda_handler"
  runtime          = "python3.9"
  timeout          = 30
  
  environment {
    variables = {
      NOTEBOOK_NAME = var.notebook_name
      ACTION        = "start"
    }
  }
  
  filename         = "lambda_function.zip"
  source_code_hash = filebase64sha256("lambda_function.zip")
  
  # Inline Lambda code
  # Note: For production, use a proper deployment package
  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

# EventBridge rule to stop notebook
resource "aws_cloudwatch_event_rule" "stop_rule" {
  name                = "neptune_workbench_stop_rule"
  description         = "Stop Neptune workbench at 7 PM IST on weekdays"
  schedule_expression = var.stop_schedule
}

# EventBridge target for stop rule
resource "aws_cloudwatch_event_target" "stop_target" {
  rule      = aws_cloudwatch_event_rule.stop_rule.name
  target_id = "StopNeptuneWorkbench"
  arn       = aws_lambda_function.stop_notebook.arn
}

# EventBridge rule to start notebook
resource "aws_cloudwatch_event_rule" "start_rule" {
  name                = "neptune_workbench_start_rule"
  description         = "Start Neptune workbench at 9 AM IST on weekdays"
  schedule_expression = var.start_schedule
}

# EventBridge target for start rule
resource "aws_cloudwatch_event_target" "start_target" {
  rule      = aws_cloudwatch_event_rule.start_rule.name
  target_id = "StartNeptuneWorkbench"
  arn       = aws_lambda_function.start_notebook.arn
}

# Lambda permission for EventBridge to invoke stop function
resource "aws_lambda_permission" "allow_eventbridge_stop" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.stop_notebook.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.stop_rule.arn
}

# Lambda permission for EventBridge to invoke start function
resource "aws_lambda_permission" "allow_eventbridge_start" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.start_notebook.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.start_rule.arn
}
