'''
Settings.py

All configuration comes from environment variables here, in one place. Nothing else reads the environment.
'''
import os
from dataclasses import dataclass

from psycopg.conninfo import make_conninfo


@dataclass(frozen=True)
class Settings:
    adminUsername: str
    adminPassword: str
    adminEmail: str
    postgresHost: str
    postgresPort: str
    postgresUser: str
    postgresPassword: str
    mongoUri: str
    mongoDatabase: str
    staticDir: str
    sessionSeconds: int = 12 * 60 * 60
    loginMaxFailures: int = 5
    registerMaxPerWindow: int = 10
    limitWindowSeconds: int = 60

    @staticmethod
    def fromEnv() -> "Settings":
        env = os.environ.get
        return Settings(
            adminUsername=env("ADMIN_USERNAME", "adminUsername"),
            adminPassword=env("ADMIN_PASSWORD", "password"),
            adminEmail=env("ADMIN_EMAIL", "admin@example.com"),
            postgresHost=env("POSTGRES_HOST", "localhost"),
            postgresPort=env("POSTGRES_PORT", "5432"),
            postgresUser=env("POSTGRES_USER", "postgres"),
            postgresPassword=env("POSTGRES_PASSWORD", "changeme"),
            mongoUri=env("MONGO_URI", "mongodb://localhost:27018"),
            mongoDatabase=env("MONGO_DATABASE", "UserFiles"),
            staticDir=env("STATIC_DIR", "dist"),
        )

    def conninfo(self, database: str) -> str:
        return make_conninfo(host=self.postgresHost, port=self.postgresPort, user=self.postgresUser,
                             password=self.postgresPassword, dbname=database)
