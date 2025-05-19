import valkey

from config import Settings

settings = Settings()
redis = valkey.Valkey(host=settings.cache_host, port=settings.cache_port, db=settings.cache_db)


def get_from_cache(key: str):
    try:
        return redis.get(key)
    except valkey.exceptions.ConnectionError:
        return None

    except Exception as e:
        return None


def set_in_cache(key: str, value: str, ttl: int = 60):
    try:
        redis.set(key, value)
        redis.expire(key, ttl)

    except valkey.exceptions.ConnectionError:
        return None

    except Exception as e:
        return None
