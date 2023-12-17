from redis import Redis

from enrollment_notification_service.models import (
    QueryStatus,
    SubscriptionRequest,
    UnSubscribeRequest,
    SubscriptionCourse,
)


class RedisQueryException(Exception):
    pass


def create_subscription(subscription_request: SubscriptionRequest, redis_client: Redis):
    key = f"student_id:{subscription_request.student_id}|course_code:{subscription_request.course_code}"
    subscription_body = {
        "email": subscription_request.email,
        "webhook_url": str(subscription_request.webhook_url),
    }
    try:
        exists_count = redis_client.exists(key)
        if exists_count == 1:
            existing_email = redis_client.hget(key, "email")
            existing_webhook_url = redis_client.hget(key, "webhook_url")
            if existing_email != subscription_request.email:
                keys = ["email"]
                redis_client.hdel(key, *keys)  # type:ignore
            if existing_webhook_url != str(subscription_request.webhook_url):
                keys = ["webhook_url"]
                redis_client.hdel(key, *keys)  # type:ignore

        redis_client.hset(key, mapping=subscription_body)
    except Exception as e:
        raise RedisQueryException(QueryStatus.SUBSCRIPTION_FAILED) from e
    return QueryStatus.SUBSCRIPTION_SUCCESS


def delete_subscrition(unsubsribe_request: UnSubscribeRequest, redis_client: Redis):
    key = f"student_id:{unsubsribe_request.student_id}|course_code:{unsubsribe_request.course_code}"
    try:
        exists_count = redis_client.exists(key)
        if exists_count == 0:
            return QueryStatus.KEY_NOT_FOUND
        redis_client.delete(key)
        return QueryStatus.UNSUBSCRIBE_SUCCESS
    except Exception as e:
        raise RedisQueryException(QueryStatus.UNSUBSCRIBE_SUCCESS) from e


def list_subscriptions(student_id: str, redis_client: Redis):
    key = f"student_id:{student_id}|*"
    subscription_courses = []
    try:
        list_keys = []
        for key in redis_client.scan_iter(key):
            list_keys.append(key)
        for key in list_keys:
            key_token = key.split("|")
            course_code = key_token[1].split(":")[1]
            email = redis_client.hget(key, "email")
            webhook_url = redis_client.hget(key, "webhook_url")
            subscription_courses.append(
                SubscriptionCourse(
                    course_code=course_code, email=email, webhook_url=webhook_url
                )
            )  # type:ignore
    except Exception as e:
        raise RedisQueryException(QueryStatus.LIST_SUBSCRIPTION_FAILED) from e
    return subscription_courses
