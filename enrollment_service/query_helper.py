''' This file contains the query for the enrollment service.'''
from botocore.exceptions import ClientError
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer
import random 

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
    ids = []
    instructor_id = {}
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
            ids = [{'id': item['GSI1_SK']['S'].split("#")[-1]} for item in items]
            python_data = [{ k: deserializer.deserialize(v) if isinstance(v, dict) else v for k, v in item.items()} for item in formatted_response]        
            final_response = []

            for item in python_data:
                # append ids from id to item['Detail']
                item['Detail'].update(ids[python_data.index(item)])
                final_response.append(item['Detail'])
            print("Query successful.")
        else:
            return None
    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])    
    # Get instructor id for each class
    non_dupes_class_id = list(set([item['id'] for item in final_response]))
    for class_id in non_dupes_class_id:
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
            if len(response['Items']) > 0:
                item = response['Items']
                class_id = item[0]['GSI3_PK']['S'].split("c#")[1]
                instructor_uid = item[0]['GSI3_SK']['S'].split("i#")[1]
                instructor_id[class_id] = instructor_uid
                print("Query successful.")
            else:
                return None
        except ClientError as error:
            handle_error(error)
            return None
        except BaseException as error:
            print("Unknown error while querying: " + error.response['Error']['Message'])
            return None
    # Add instructor id to each class
    for item in final_response:
        if item['id'] in instructor_id:
            item['instructorId'] = instructor_id[item['id']]
    return final_response

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
            ids = [{'id': item['PK']['S'].split("#")[-1]} for item in items]
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
        if len(response['Items']) > 0:
            item = response['Items']
            class_data = {k: deserializer.deserialize(v) for k,v in item[0].items()}
            # Get rid off PK and SK from class_data and add id as key
            class_data['id'] = item[0]['PK']['S'].split("#")[-1]
            class_data['instructorId'] = item[0]['GSI3_SK']['S'].split("i#")[1]
            class_data = {k: class_data[k] for k in class_data if k not in ['PK', 'SK', 'EntityType']}
            print("Query successful.")
        else:
            return None
    except ClientError as error:
        handle_error(error)
        return None
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])
        return None
    return class_data

"""Check if class exists"""
def check_class_exists(dynamodb_client, class_id):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"c#{class_id}"}
        }
    }
    try:
        response = dynamodb_client.get_item(**input)
        # Parse data from response
        if "Item" in response:
            print("Query successful.")
            return True
        else:
            return False
    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])

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
        "IndexName": "GSI2",
        "KeyConditionExpression": "#77100 = :77100 And #77101 = :77101",
        "ExpressionAttributeNames": {"#77100":"GSI2_PK","#77101":"GSI2_SK"},
        "ExpressionAttributeValues": {":77100": {"S":f"i#{instructor_id}"},":77101": {"S":f"c#{class_id}"}}
    }
    try:
        response = dynamodb_client.query(**input)
        # Parse data from response
        if len(response['Items']) > 0:
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

""" Query all students for a class """
def query_all_students(dynamodb_client, class_id):
    input = {
        "TableName": "TitanOnlineEnrollment",
        "KeyConditionExpression": "#cd420 = :cd420 And begins_with(#cd421, :cd421)",
        "ExpressionAttributeNames": {"#cd420":"PK","#cd421":"SK"},
        "ExpressionAttributeValues": {":cd420": {"S":f"c#{class_id}"},":cd421": {"S":"s#"}}    }
    try:
        response = dynamodb_client.query(**input)
        # Parse data from response
        items = response['Items']
        if items:
            formatted_response = [{'StudentId': item['SK']} for item in items]
            student_ids = [{ k: deserializer.deserialize(v) if isinstance(v, dict) else v for k, v in item.items()} for item in formatted_response]        
            # Create list of student ids from student_ids
            student_ids = [student_id["StudentId"] for student_id in student_ids]
            return student_ids
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
        if len(items) > 0:
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
def drop_student_from_class(dynamodb_client, student_id, class_id):
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
    print("Detail:", class_detail)
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


""" Create class """
def create_class(dynamodb_client, class_detail):
    print(class_detail)
    serialized_class_detail = {k: serializer.serialize(v) for k,v in class_detail}
    # Remove maxEnroll, instructorId  from serialized_class_detail and store in filtered_class_detail
    filtered_class_detail = {k: serialized_class_detail[k] for k in serialized_class_detail if k not in ['maxEnroll', 'InstructorId']}
    # Auto generate class_id, make sure it's unique
    class_id = random.randint(1000, 9999)
    while check_class_exists(dynamodb_client, class_id):
        class_id = random.randint(1000, 9999)
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Item": {
            "PK": {"S":f"c#{class_id}"},
            "SK": {"S":f"c#{class_id}"},
            "EntityType": {"S":"class"},
            "Detail": {"M": filtered_class_detail},
            "currentEnroll": {"N":"0"},
            "maxEnroll": {"N":str(serialized_class_detail['maxEnroll']['N'])},
            "Frozen": {"BOOL": False},
            "GSI3_PK": {"S":f"c#{class_id}"},
            "GSI3_SK": {"S":f"i#{serialized_class_detail['InstructorId']['S']}"}
        }
    }
    try:
        response = dynamodb_client.put_item(**input)
        print("Put successful.")
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while putting: " + error.response['Error']['Message'])
        return False
    
    """ Add instructor to class with PK is class_id and SK is instructor_id """
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Item": {
            "PK": {"S":f"c#{class_id}"},
            "SK": {"S":f"i#{serialized_class_detail['InstructorId']['S']}"},
            "GSI2_PK": {"S":f"i#{serialized_class_detail['InstructorId']['S']}"},
            "GSI2_SK": {"S":f"c#{class_id}"},
            "EntityType": {"S":"instructor"}
        }
    }
    try:
        response = dynamodb_client.put_item(**input)
        print("Put successful.")
    except ClientError as error:
        handle_error(error)
        return False
    except BaseException as error:
        print("Unknown error while putting: " + error.response['Error']['Message'])
        return False
     
    """Get any class id from student GSI1_PK is student_id and GSI1_SK starts with c#"""
    available_class_id = ""
    input = {
        "TableName": "TitanOnlineEnrollment",
        "IndexName": "GSI1",
        "KeyConditionExpression": "#ec990 = :ec990 And begins_with(#ec991, :ec991)",
        "ExpressionAttributeNames": {"#ec990":"GSI1_PK","#ec991":"GSI1_SK"},
        "ExpressionAttributeValues": {":ec990": {"S":f"s#0001"},":ec991": {"S":"c#"}}
    }
    try:
        response = dynamodb_client.query(**input)
        # Parse data from response
        items = response['Items']
        if items:
            available_class_id = items[0]['GSI1_SK']['S'].split("#")[-1]
            print("Query successful.")
        else:
            return None

    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])

    print("Available class id: " + available_class_id)

    """Get all student ids from available_class_id"""
    input = {
        "TableName": "TitanOnlineEnrollment",
        "KeyConditionExpression": "#cd420 = :cd420 And begins_with(#cd421, :cd421)",
        "ExpressionAttributeNames": {"#cd420":"PK","#cd421":"SK"},
        "ExpressionAttributeValues": {":cd420": {"S":f"c#{available_class_id}"},":cd421": {"S":"s#"}}
    }
    student_ids = []
    try:
        response = dynamodb_client.query(**input)
        # Parse data from response
        items = response['Items']
        if items:
            formatted_response = [{'StudentId': item['GSI1_PK']} for item in items]
            print("Formatted response: " + str(formatted_response))
            # ids = [{'id': item['PK']['S'].split("c#")[1]} for item in items]
            student_ids = [{ k: deserializer.deserialize(v) if isinstance(v, dict) else v for k, v in item.items()} for item in formatted_response]        
            # Create list of student ids from student_ids
            student_ids = [student_id["StudentId"] for student_id in student_ids]
        else:
            return None
    except ClientError as error:
        handle_error(error)
    except BaseException as error:
        print("Unknown error while querying: " + error.response['Error']['Message'])

    ### Batch add student from student_ids to class with EntityType as enrollment and GSI1_PK as s#student_id and GSI1_SK as c#open#class_id
    ### Also add class to student with EntityType as enrollment and GSI1_PK as c#class_id and GSI1_SK as s#student_id
    print(student_ids)
    for student_id in student_ids:
        input = {
            "TableName": "TitanOnlineEnrollment",
            "Item": {
                "PK": {"S":f"c#{class_id}"},
                "SK": {"S":f"{student_id}"},
                "GSI1_PK": {"S":f"{student_id}"},
                "GSI1_SK": {"S":f"c#open#{class_id}"},
                "Detail": {"M": filtered_class_detail},
                "EntityType": {"S":"enrollment"}
            }
        }
        print(input)
        try:
            response = dynamodb_client.put_item(**input)
            print("Put successful.")
        except ClientError as error:
            handle_error(error)
            return False
        except BaseException as error:
            print("Unknown error while putting: " + error.response['Error']['Message'])
            return False
    return True

"""Delete class"""
def delete_class(dynamodb_client, class_id):
    # Get class instructor id
    class_detail = query_class(dynamodb_client, class_id)
    instructor_id = class_detail['instructorId']
    # Get all student ids from class
    student_ids = query_all_students(dynamodb_client, class_id)
    # Delete class
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"c#{class_id}"}
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
    # Delete instructor
    input = {
        "TableName": "TitanOnlineEnrollment",
        "Key": {
            "PK": {"S":f"c#{class_id}"}, 
            "SK": {"S":f"i#{class_id}"}
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
    # Delete all enrollment
    for student_id in student_ids:
        input = {
            "TableName": "TitanOnlineEnrollment",
            "Key": {
                "PK": {"S":f"c#{class_id}"}, 
                "SK": {"S":f"{student_id}"}
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
    return True
