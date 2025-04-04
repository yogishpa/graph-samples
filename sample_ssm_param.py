import boto3
from gremlin_python.driver import client
from gremlin_python.driver.protocol import GremlinServerError
import os
import json
import botocore
from botocore.config import Config
from gremlin_python.structure.graph import Path

class GremlinEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return {'labels': obj.labels, 'objects': obj.objects}
        return json.JSONEncoder.default(self, obj)

class GremlinQueryExecutor:
    def __init__(self):
        # Set AWS region - update this to your region if different
        self.region = 'us-east-1'
        
        # Configure AWS with region settings
        self.aws_config = Config(
            region_name=self.region,
            retries=dict(
                max_attempts=2
            )
        )
        
        # Set environment variable for AWS region
        os.environ['AWS_DEFAULT_REGION'] = self.region
        
        # Initialize AWS session with region
        self.session = boto3.Session(region_name=self.region)
        
        # Initialize AWS SSM client with config
        self.ssm_client = self.session.client('ssm', config=self.aws_config)
        
        # Get Neptune endpoint - update this to your Neptune endpoint
        self.neptune_endpoint = f"YOUR_NEPTUNE_END_POINT"
        if not self.neptune_endpoint:
            raise ValueError("Neptune endpoint is not set")

    def serialize_result(self, result):
        """Helper method to serialize Neptune results"""
        if isinstance(result, (list, tuple)):
            return [self.serialize_result(item) for item in result]
        elif isinstance(result, dict):
            return {k: self.serialize_result(v) for k, v in result.items()}
        elif isinstance(result, Path):
            return {
                'labels': result.labels,
                'objects': self.serialize_result(result.objects)
            }
        elif hasattr(result, '__dict__'):
            return self.serialize_result(result.__dict__)
        else:
            return result

    def get_query_from_parameter_store(self, parameter_name):
        try:
            response = self.ssm_client.get_parameter(
                Name=parameter_name,
                WithDecryption=True
            )
            return response['Parameter']['Value']
        except botocore.exceptions.ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            if error_code == 'AccessDeniedException':
                print("IAM Role requires the following permissions:")
                print(f"""
                {{
                    "Version": "2012-10-17",
                    "Statement": [
                        {{
                            "Effect": "Allow",
                            "Action": [
                                "ssm:GetParameter",
                                "ssm:GetParameters"
                            ],
                            "Resource": "arn:aws:ssm:{self.region}:YOUR_AWS_ACCOUNT_ID:parameter/app/gremlin/*"
                        }}
                    ]
                }}
                """)
            raise Exception(f"AWS Error: {str(e)}")
        except Exception as e:
            raise Exception(f"Error retrieving parameter: {str(e)}")

    def execute_gremlin_query(self, query):
        try:
            # Configure Gremlin client with region-specific endpoint
            connection_string = f'wss://{self.neptune_endpoint}:8182/gremlin'
            
            # Initialize Gremlin client
            gremlin_client = client.Client(
                connection_string,
                'g'
            )

            try:
                # Execute the query
                result = gremlin_client.submit(query).all().result()
                # Serialize the result
                serialized_result = self.serialize_result(result)
                return serialized_result
            finally:
                gremlin_client.close()
        except GremlinServerError as e:
            raise Exception(f"Gremlin query execution failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Connection error: {str(e)}")

def main():
    try:
        # Initialize the executor
        executor = GremlinQueryExecutor()

        # For testing with Parameter Store
        try:
            parameter_name = '/app/gremlin/query1'
            query = executor.get_query_from_parameter_store(parameter_name)
        except Exception as e:
            print(f"Parameter Store access failed: {str(e)}")
            print("Falling back to direct query...")
            # Fallback to direct query if Parameter Store access fails
            query = "g.V().limit(1)"  # Replace with your actual Gremlin query

        # Execute the query
        result = executor.execute_gremlin_query(query)

        # Process the results
        print("Query Results:")
        print(json.dumps(result, indent=2, cls=GremlinEncoder))

    except Exception as e:
        print(f"Error: {str(e)}")

def print_results(results):
    """Helper function to print results in a readable format"""
    try:
        if isinstance(results, (list, tuple)):
            for item in results:
                print_results(item)
        elif isinstance(results, dict):
            for key, value in results.items():
                print(f"{key}: ", end="")
                print_results(value)
        else:
            print(results)
    except Exception as e:
        print(f"Error printing results: {str(e)}")

if __name__ == "__main__":
    # Set AWS region at script level
    boto3.setup_default_session(region_name='us-east-1')  # Update this to your region if different
    main()
