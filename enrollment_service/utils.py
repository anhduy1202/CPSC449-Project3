import datetime
from redis import Redis


def new_timestamp():
    return datetime.now().strftime("%a, %d %b %Y %H:%M:%S GMT")


class QueryStatus:
    UPDATE_SUCCESS = "Update Success"
    UPDATE_FAILED = "Update Failed"


def update_last_modified(class_id: str, redis_client: Redis):
    key = f"class_id:{class_id}"
    try:
        redis_client.hset(key, "last-modified", new_timestamp())
    except Exception as e:
        raise Exception(QueryStatus.UPDATE_FAILED) from e
    return QueryStatus.UPDATE_SUCCESS


def get_last_modified(class_id: str, redis_client: Redis):
    key = f"class_id:{class_id}"
    try:
        exists_count = redis_client.exists(key)
        if exists_count == 0:
            timestamp = new_timestamp()
            redis_client.hset(key, "last-modified", timestamp)
        else:
            timestamp = redis_client.hget(key, "last-modified")
    except Exception as e:
        raise Exception(QueryStatus.UPDATE_FAILED) from e
    return timestamp
