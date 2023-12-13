### Enrollment Notification Service

#### Redis
- Redis is used to store subscription created by student, the data structure look like below
```
student_id:{1}|course_code:{CPSC_409} {email:{abc@gmail.com}, webhook_url: {http://foo.com}}
```
- It contains key as student_id:{1}|course_code:{CPSC_409} and mapping as {email:{abc@gmail.com}, webhook_url: {http://foo.com}}
- It uses HSET to create key

### REST API
- /subscribe
```
Method : POST
# Request Schema
{
  "student_id": "string",
  "course_code": "string",
  "email": "user@example.com",
  "webhook_url": "https://example.com/"
}
# Response Schema
{
  "status": "string",
  "course_code": "string"
}
```

- /unsubscribe
```
Method : Delete
# Request Schema
{
  "student_id": "string",
  "course_code": "string"
}
# Response Schema
{
  "status": "string",
  "course_code": "string"
}
```

- /list_subscriptions/{student_id}
```
Method: GET
# Response Schema
{
  "subscribed_courses": []
}
```

### Start service
```
./run.sh
```