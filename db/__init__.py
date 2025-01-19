from config.settings import Settings
from db.basedb import BaseDB
from db.postgresql import PostgreSQLDB
from db.sqlite import SQLiteDB


def create_db(settings: Settings) -> BaseDB:
    """
    Factory function to create appropriate database instance based on settings.

    Args:
        settings: Settings instance containing database configuration

    Returns:
        BaseDB: Configured database instance

    Raises:
        ValueError: If DB_TYPE is not supported
    """
    if settings.DB_TYPE.lower() == "sqlite":
        db = SQLiteDB(settings.DB_NAME)
        db.setup_database()
        return db

    elif settings.DB_TYPE.lower() == "postgresql":
        # Validate required PostgreSQL settings
        required_fields = [
            settings.PSQL_DB_HOST,
            settings.PSQL_DB_PORT,
            settings.PSQL_DB_DATABASE,
            settings.PSQL_DB_USER,
            settings.PSQL_DB_PASSWORD,
        ]

        if any(field is None for field in required_fields):
            raise ValueError(
                "Missing required PostgreSQL configuration. "
                "Please check your environment variables or .env file."
            )

        connection_config = {
            "host": settings.PSQL_DB_HOST,
            "port": settings.PSQL_DB_PORT,
            "database": settings.PSQL_DB_DATABASE,
            "user": settings.PSQL_DB_USER,
            "password": settings.PSQL_DB_PASSWORD,
        }

        db = PostgreSQLDB(connection_config)
        db.setup_database()
        return db

    else:
        raise ValueError(
            f"Unsupported database type: {settings.DB_TYPE}. "
            "Supported types are: 'sqlite', 'postgresql'"
        )
