from typing import Any, Type

from models.users import User
from tortoise.signals import post_save


@post_save(User)
async def user_post_save(
    sender: Type[User],
    instance: User,
    created: bool,
    using_db: Any,
    update_fields: list,
) -> None:
    if created:
        print(f"New user created: {instance.username}")
    else:
        print(f"User updated: {instance.username}")
        if update_fields:
            print(f"Updated fields: {update_fields}")
