import uvicorn
from uvicorn.server import Server
from fastapi import FastAPI, HTTPException, status, Header
from asyncio import run
from enrollment_notification_service.models import ListSubscriptionResponse, QueryStatus, SubscriptionRequest,SubscriptionResponse, UnSubscribeRequest, ListSubscriptionRequest
from enrollment_notification_service.redis_query import RedisQueryException, create_subscription, delete_subscrition, list_subscriptions
import redis

app = FastAPI()
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

@app.post(path="/subscribe", operation_id="subscribe_notification", response_model = SubscriptionResponse)
async def subscribe_notification(subscription_request: SubscriptionRequest):
    if subscription_request.email is None and subscription_request.webhook_url is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Must provide email or webhook url")
    try:
         result = create_subscription(subscription_request, redis_client)
    except RedisQueryException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Interval server error')
    return SubscriptionResponse(status= result, course_code=subscription_request.course_code)

@app.delete(path="/unsubcribe", operation_id="unsubscribe_notification", response_model = SubscriptionResponse)
async def unsubscribe_notification(unsubscribe_request: UnSubscribeRequest):
    try:
         result = delete_subscrition(unsubscribe_request, redis_client)
    except RedisQueryException as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Interval server error')
    return SubscriptionResponse(status= result, course_code=unsubscribe_request.course_code)

@app.get(path="/list_subscriptions/{student_id}", operation_id = "list_subscriptions_notification", response_model = ListSubscriptionResponse)
async def list_subscriptions_notification(student_id: str):
    try:
        result = list_subscriptions(student_id, redis_client)
    except RedisQueryException:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Internal server error')
    return ListSubscriptionResponse(subscribed_courses=result)

    
async def main():
    """Start the server."""
    server = Server(uvicorn.Config(app=app, host="0.0.0.0", timeout_graceful_shutdown=30))
    await server.serve()

if __name__ == "__main__":
    run(main())