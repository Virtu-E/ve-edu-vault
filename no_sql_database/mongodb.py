from django.conf import settings

from no_sql_database.nosql_database_engine import MongoDatabaseEngine

mongo_database = MongoDatabaseEngine(getattr(settings, "MONGO_URL", None))
