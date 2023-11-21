''' This file contains the query for the enrollment service.'''
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer
import ast
deserializer = TypeDeserializer()

ERROR_HELP_STRINGS = {
    # Common Errors
    'InternalServerError': 'Internal Server Error, generally safe to retry with exponential back-off',
    'ProvisionedThroughputExceededException': 'Request rate is too high. If you\'re using a custom retry strategy make sure to retry with exponential back-off.' +
                                              'Otherwise consider reducing frequency of requests or increasing provisioned capacity for your table or secondary index',
    'ResourceNotFoundException': 'One of the tables was not found, verify table exists before retrying',
    'ServiceUnavailable': 'Had trouble reaching DynamoDB. generally safe to retry with exponential back-off',
    'ThrottlingException': 'Request denied due to throttling, generally safe to retry with exponential back-off',
    'UnrecognizedClientException': 'The request signature is incorrect most likely due to an invalid AWS access key ID or secret key, fix before retrying',
    'ValidationException': 'The input fails to satisfy the constraints specified by DynamoDB, fix input before retrying',
    'RequestLimitExceeded': 'Throughput exceeds the current throughput limit for your account, increase account level throughput before retrying',
}

def handle_error(error):
    error_code = error.response['Error']['Code']
    error_message = error.response['Error']['Message']

    error_help_string = ERROR_HELP_STRINGS[error_code]

    print('[{error_code}] {help_string}. Error message: {error_message}'
          .format(error_code=error_code,
                  help_string=error_help_string,
                  error_message=error_message))



"""Query for available classes given student id"""
def query_available_classes(dynamodb_client, student_id):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "IndexName": "GSI1",
        "KeyConditionExpression": "#ec990 = :ec990 And begins_with(#ec991, :ec991)",
        "ExpressionAttributeNames": {"#ec990":"GSI1_PK","#ec991":"GSI1_SK"},
        "ExpressionAttributeValues": {":ec990": {"S":f"s#{student_id}"},":ec991": {"S":"c#open#"}}
    }
    try:
        response = dynamodb_client.query(**input)
        # Parse data from response
        items = response['Items']
        if items:
            formatted_response = [{'Detail': item['Detail']} for item in items]
            ids = [{'id': item['PK']['S'].split("c#")[1]} for item in items]
            python_data = [{ k: deserializer.deserialize(v) if isinstance(v, dict) else v for k, v in item.items()} for item in formatted_response]        
            final_response = []

            for item in python_data:
                # append ids from id to item['Detail']
                item['Detail'].update(ids[python_data.index(item)])
                final_response.append(item['Detail'])
            print("Query successful.")
        else:
            return None

        return final_response

    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])

"""Query for enrolled classes given student id"""
def query_enrolled_classes(dynamodb_client, student_id):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "IndexName": "GSI1",
        "KeyConditionExpression": "#ec990 = :ec990 And begins_with(#ec991, :ec991)",
        "ExpressionAttributeNames": {"#ec990":"GSI1_PK","#ec991":"GSI1_SK"},
        "ExpressionAttributeValues": {":ec990": {"S":f"s#{student_id}"},":ec991": {"S":"c#enrolled#"}}
    }
    try:
        response = dynamodb_client.query(**input)
        # Parse data from response
        items = response['Items']
        if items:
            formatted_response = [{'Detail': item['Detail']} for item in items]
            ids = [{'id': item['PK']['S'].split("c#")[1]} for item in items]
            python_data = [{ k: deserializer.deserialize(v) if isinstance(v, dict) else v for k, v in item.items()} for item in formatted_response]        
            final_response = []

            for item in python_data:
                # append ids from id to item['Detail']
                item['Detail'].update(ids[python_data.index(item)])
                final_response.append(item['Detail'])
            print("Query successful.")
        else:
            return None

        return final_response

    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])


"""Query for student given student id"""
def query_student(dynamodb_client, student_id):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"s#{student_id}"}, 
            "SK": {"S":f"s#{student_id}"}
        }
    }
    try:
        response = dynamodb_client.get_item(**input)
        # Parse data from response
        if "Item" in response:
            item = response['Item']
            student_data = {k: deserializer.deserialize(v) for k,v in item.items()}
            # Get rid off PK and SK from student_data and add id as key
            student_data['id'] = item['PK']['S'].split("s#")[1]
            student_data = {k: student_data[k] for k in student_data if k not in ['PK', 'SK', 'EntityType']}
            print("Query successful.")
        else:
            return None
        return student_data
    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])