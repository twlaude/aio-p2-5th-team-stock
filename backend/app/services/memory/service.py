from app.clients.redis import client as redis_client
from app.repositories import user_repository
from app.schemas.memory import MemoryView


async def get_memory(user_id: str) -> MemoryView:
    record = await user_repository.get_by_id(user_id)
    long_term = record.profile if record else None
    return MemoryView(user_id=user_id, long_term=long_term, short_term=await redis_client.get_state(user_id))


async def clear_memory(user_id: str) -> None:
    await user_repository.delete_profile(user_id)
    await redis_client.clear_state(user_id)
