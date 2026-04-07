from app.core.config import get_settings
from app.db.store import InMemoryStore, MongoStore
from app.services.seeder import seed_demo_data


def run_seed() -> None:
    settings = get_settings()
    if settings.mongodb_uri:
        store = MongoStore(settings.mongodb_uri, settings.mongodb_db_name)
    else:
        store = InMemoryStore()
    seed_demo_data(store)


if __name__ == "__main__":
    run_seed()
