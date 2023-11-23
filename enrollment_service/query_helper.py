''' This file contains the query for the enrollment service.'''
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
import ast
deserializer = TypeDeserializer()
serializer = TypeSerializer()

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
    final_response = []
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

""" Query for student given student ids using batch_get_item """
def batch_query_student(dynamodb_client, student_ids):
    input = {
        "RequestItems": {
            "TitanOnlineEnrollment": {
                "Keys": [{"PK": {"S":f"{student_id}"}, "SK": {"S":f"{student_id}"}} for student_id in student_ids]
            }
        }
    }
    try:
        response = dynamodb_client.batch_get_item(**input)
        # Parse data from response
        if "Responses" in response:
            items = response['Responses']['TitanOnlineEnrollment']
            ids = [{'id': item['PK']['S'].split("s#")[1]} for item in items]
            print(ids)
            student_infos = [{ k: deserializer.deserialize(v) if isinstance(v, dict) else v for k, v in item.items()} for item in items]        
            final_response = []
            # Format response
            for item in student_infos:
                # append ids from id, remove SK, EntityType, and PK
                item.update(ids[student_infos.index(item)])
                item.pop('SK', None)
                item.pop('EntityType', None)
                item.pop('PK', None)
                final_response.append(item)
            print("Query successful.")
        else:
            return None
        return final_response
    
    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])

"""Query for class given class id"""
def query_class(dynamodb_client, class_id):
    class_data = {}
    input = {
        "TableName": "TitanOnlineEnrollment",
        "IndexName": "GSI3",
        "KeyConditionExpression": "#e55c0 = :e55c0 And begins_with(#e55c1, :e55c1)",
        "ExpressionAttributeNames": {"#e55c0":"GSI3_PK","#e55c1":"GSI3_SK"},
        "ExpressionAttributeValues": {":e55c0": {"S":f"c#{class_id}"},":e55c1": {"S":"i#"}}
    }
    try:
        response = dynamodb_client.query(**input)
        # Parse data from response
        if "Items" in response:
            item = response['Items']
            class_data = {k: deserializer.deserialize(v) for k,v in item[0].items()}
            # Get rid off PK and SK from class_data and add id as key
            class_data['id'] = item[0]['PK']['S'].split("c#")[1]
            class_data['instructorId'] = item[0]['GSI3_SK']['S'].split("i#")[1]
            class_data = {k: class_data[k] for k in class_data if k not in ['PK', 'SK', 'EntityType']}
            print("Query successful.")
        else:
            return None
    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])
    return class_data

"""Update currentEnroll for a class"""
def update_current_enroll(dynamodb_client, class_id, new_enroll):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"c#{class_id}"}
        },
        "UpdateExpression": "SET #ec992 = :ec992",
        "ExpressionAttributeNames": {"#ec992":"currentEnroll"},
        "ExpressionAttributeValues": {":ec992": {"N":str(new_enroll)}}
    }
    try:
        response = dynamodb_client.update_item(**input)
        print("Update successful.")
        return True
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while updating: " + error.response['Error']['Message'])
        return False

"""Update enrolled class for a student"""
def update_enrolled_class(dynamodb_client, student_id, class_id):
    # delete PK of c#class_id and SK of s#student_id and s#dropped#student_id if exists
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"s#{student_id}"}
        }
    }
    try:
        response = dynamodb_client.delete_item(**input)
        print("Delete successful.")
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while deleting: " + error.response['Error']['Message'])
        return False
    
    input = {
    "TableName": "TitanOnlineEnrollment",
    "Key": {
        "PK": {"S":f"c#{class_id}"}, 
        "SK": {"S":f"s#dropped#{student_id}"}
    }
}
    try:
        response = dynamodb_client.delete_item(**input)
        print("Delete successful.")
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while deleting: " + error.response['Error']['Message'])
        return False
    

    # add new entry of c#class_id and s#enrolled#student_id with GSI1_PK as s#student_id and GSI1_SK as c#enrolled#class_id
    class_detail = query_class(dynamodb_client, class_id)
    serialized_class_detail = {k: serializer.serialize(v) for k,v in class_detail.items()}
    print(serialized_class_detail)
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Item": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"s#enrolled#{student_id}"},
            "GSI1_PK": {"S":f"s#{student_id}"},
            "GSI1_SK": {"S":f"c#enrolled#{class_id}"},
            "EntityType": {"S":"enrollment"},
            "Detail": serialized_class_detail['Detail']
        }
    }

    try:
        response = dynamodb_client.put_item(**input)
        print("Put successful.")
        print(response)
        return True
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while putting: " + error.response['Error']['Message'])
        return False

"""Query for instructor given instructor id"""
def query_instructor(dynamodb_client, instructor_id):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"i#{instructor_id}"}, 
            "SK": {"S":f"i#{instructor_id}"}
        }
    }
    try:
        response = dynamodb_client.get_item(**input)
        # Parse data from response
        if "Item" in response:
            item = response['Item']
            instructor_data = {k: deserializer.deserialize(v) for k,v in item.items()}
            # Get rid off PK and SK from instructor_data and add id as key
            instructor_data['id'] = item['PK']['S'].split("i#")[1]
            instructor_data = {k: instructor_data[k] for k in instructor_data if k not in ['PK', 'SK', 'EntityType']}
            print("Query successful.")
        else:
            return None
        return instructor_data
    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])

"""Query to see if the class belongs to the instructor"""
def query_class_instructor(dynamodb_client, instructor_id, class_id):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "KeyConditionExpression": "#cd420 = :cd420 And begins_with(#cd421, :cd421)",
        "ExpressionAttributeNames": {"#cd420":"PK","#cd421":"SK"},
        "ExpressionAttributeValues": {":cd420": {"S":f"c#{class_id}"},":cd421": {"S":"s#enrolled"}}    }
    try:
        response = dynamodb_client.query(**input)
        # Parse data from response
        if "Items" in response:
            item = response['Items']
            # student_data = {k: deserializer.deserialize(v) for k,v in item.items()}
            print(item)
            return True
        else:
            return False
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])
        return False
    
""" Query enrolled students for a class """
def query_enrolled_students(dynamodb_client, class_id):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "KeyConditionExpression": "#cd420 = :cd420 And begins_with(#cd421, :cd421)",
        "ExpressionAttributeNames": {"#cd420":"PK","#cd421":"SK"},
        "ExpressionAttributeValues": {":cd420": {"S":f"c#{class_id}"},":cd421": {"S":"s#enrolled"}}    }
    try:
        response = dynamodb_client.query(**input)
        # Parse data from response
        items = response['Items']
        if items:
            formatted_response = [{'StudentId': item['GSI1_PK']} for item in items]
            # ids = [{'id': item['PK']['S'].split("c#")[1]} for item in items]
            student_ids = [{ k: deserializer.deserialize(v) if isinstance(v, dict) else v for k, v in item.items()} for item in formatted_response]        
            # Create list of student ids from student_ids
            student_ids = [student_id["StudentId"] for student_id in student_ids]
            # Get each student's info from student ids and append to final_response
            student_info = batch_query_student(dynamodb_client, student_ids)
            return student_info
        else:
            return None

    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])

""" Query dropped students for a class """
def query_dropped_students(dynamodb_client, class_id):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "KeyConditionExpression": "#cd420 = :cd420 And begins_with(#cd421, :cd421)",
        "ExpressionAttributeNames": {"#cd420":"PK","#cd421":"SK"},
        "ExpressionAttributeValues": {":cd420": {"S":f"c#{class_id}"},":cd421": {"S":"s#dropped"}}    }
    try:
        response = dynamodb_client.query(**input)
        # Parse data from response
        items = response['Items']
        if items:
            formatted_response = [{'StudentId': item['GSI1_PK']} for item in items]
            # ids = [{'id': item['PK']['S'].split("c#")[1]} for item in items]
            student_ids = [{ k: deserializer.deserialize(v) if isinstance(v, dict) else v for k, v in item.items()} for item in formatted_response]        
            # Create list of student ids from student_ids
            student_ids = [student_id["StudentId"] for student_id in student_ids]
            # Get each student's info from student ids and append to final_response
            student_info = batch_query_student(dynamodb_client, student_ids)
            return student_info
        else:
            return None

    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])

""" Freeze enrollment for a class """
def freeze_enrollment(dynamodb_client, class_id):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"c#{class_id}"}
        },
        "UpdateExpression": "SET #b1540 = :b1540",
        "ExpressionAttributeNames": {"#b1540":"Frozen"},
        "ExpressionAttributeValues": {":b1540": {"BOOL": True}}
    }
    try:
        response = dynamodb_client.update_item(**input)
        print("Update successful.")
        return True
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while updating: " + error.response['Error']['Message'])
        return False
    
### Drop student from class
def drop_student_from_class(dynamodb_client, class_id, student_id):
    # delete PK of c#class_id and SK of s#enrolled#student_id if exists
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"s#enrolled#{student_id}"}
        }
    }
    try:
        response = dynamodb_client.delete_item(**input)
        print("Delete successful.")
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while deleting: " + error.response['Error']['Message'])
        return False
    

    # add new entry of c#class_id and s#dropped#student_id with GSI1_PK as s#student_id and GSI1_SK as c#open#class_id
    class_detail = query_class(dynamodb_client, class_id)
    serialized_class_detail = {k: serializer.serialize(v) for k,v in class_detail.items()}
    print(serialized_class_detail)
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Item": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"s#dropped#{student_id}"},
            "GSI1_PK": {"S":f"s#{student_id}"},
            "GSI1_SK": {"S":f"c#open#{class_id}"},
            "EntityType": {"S":"enrollment"},
            "Detail": serialized_class_detail['Detail']
        }
    }

    try:
        response = dynamodb_client.put_item(**input)
        print("Put successful.")
        return True
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while putting: " + error.response['Error']['Message'])
        return False


def change_instructor(dynamodb_client, class_id, instructor_id):
    ## Get current instructor id for class
    class_detail = query_class(dynamodb_client, class_id)
    current_instructor_id = class_detail['instructorId']
    ## Delete entry of class_id and curent_instructor_id
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"i#{current_instructor_id}"}
        }
    }
    try:
        response = dynamodb_client.delete_item(**input)
        print("Delete successful.")
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while deleting: " + error.response['Error']['Message'])
        return False
    ## Update GSI3_SK with PK c#class_id SK class_id to instructor_id
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"c#{class_id}"}
        },
        "UpdateExpression": "SET #cd421 = :cd421",
        "ExpressionAttributeNames": {"#cd421":"GSI3_SK"},
        "ExpressionAttributeValues": {":cd421": {"S":f"i#{instructor_id}"}}
    }
    try:
        response = dynamodb_client.update_item(**input)
        print("Update successful.")
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while updating: " + error.response['Error']['Message'])
        return False
    ## Add new entry of class_id and instructor_id with EntityType as instructor and GSI2_PK as i#instructor_id and GSI2_SK as c#class_id
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Item": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"i#{instructor_id}"},
            "GSI2_PK": {"S":f"i#{instructor_id}"},
            "GSI2_SK": {"S":f"c#{class_id}"},
            "EntityType": {"S":"instructor"}
        }
    }
    try:
        response = dynamodb_client.put_item(**input)
        print("Put successful.")
        return True
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while putting: " + error.response['Error']['Message'])
        return False
