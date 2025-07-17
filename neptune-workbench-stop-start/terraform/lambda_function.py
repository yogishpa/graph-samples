import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    notebook_name = os.environ['NOTEBOOK_NAME']
    action = os.environ['ACTION']
    
    sagemaker = boto3.client('sagemaker')
    
    try:
        # Check the current state of the notebook instance
        response = sagemaker.describe_notebook_instance(
            NotebookInstanceName=notebook_name
        )
        
        current_status = response['NotebookInstanceStatus']
        logger.info(f"Current status of notebook {notebook_name}: {current_status}")
        
        if action == "stop":
            # Only stop if the notebook is in 'InService' state
            if current_status == 'InService':
                logger.info(f"Stopping notebook instance: {notebook_name}")
                sagemaker.stop_notebook_instance(
                    NotebookInstanceName=notebook_name
                )
                return {
                    'statusCode': 200,
                    'body': f"Successfully initiated stop for notebook instance {notebook_name}"
                }
            else:
                logger.info(f"Notebook {notebook_name} is not in 'InService' state, current state: {current_status}")
                return {
                    'statusCode': 200,
                    'body': f"Notebook instance {notebook_name} is already in {current_status} state, no action taken"
                }
        elif action == "start":
            # Only start if the notebook is in 'Stopped' state
            if current_status == 'Stopped':
                logger.info(f"Starting notebook instance: {notebook_name}")
                sagemaker.start_notebook_instance(
                    NotebookInstanceName=notebook_name
                )
                return {
                    'statusCode': 200,
                    'body': f"Successfully initiated start for notebook instance {notebook_name}"
                }
            else:
                logger.info(f"Notebook {notebook_name} is not in 'Stopped' state, current state: {current_status}")
                return {
                    'statusCode': 200,
                    'body': f"Notebook instance {notebook_name} is already in {current_status} state, no action taken"
                }
                
    except Exception as e:
        logger.error(f"Error managing notebook instance {notebook_name}: {str(e)}")
        return {
            'statusCode': 500,
            'body': f"Error managing notebook instance: {str(e)}"
        }
