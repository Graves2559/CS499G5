'''
Container.py

Composition root: the only place that knows every concrete class. It builds the infrastructure, hands it to the
use cases through their ports, and returns the assembled services. Nothing else constructs infrastructure.
'''
import time
from dataclasses import dataclass
from typing import Optional

from UserLogin.application.UserManager import UserManager
from UserLogin.infrastructure.ScryptPasswordHasher import ScryptPasswordHasher
from UserLogin.infrastructure.UserDatabaseAdapter import UserDatabaseAdapter
from WI29_Server.application.AuthService import AuthService
from WI29_Server.application.FileService import FileService
from WI29_Server.application.GoogleSignIn import STATE_SECONDS, GoogleSignIn
from WI29_Server.infrastructure.GoogleIdentityProvider import GoogleIdentityProvider
from WI29_Server.infrastructure.MemoryStores import InMemoryPendingLogins, InMemorySessionStore, SlidingWindowLimiter
from WI29_Server.infrastructure.MongoContentStore import MongoContentStore
from WI29_Server.infrastructure.PostgresFileRepositories import PostgresFileIndex, PostgresFolderRepository
from WI29_Server.infrastructure.Settings import Settings


@dataclass
class Container:
    settings: Settings
    auth: AuthService
    files: FileService
    google: GoogleSignIn

    # The databases may still be starting when the server starts, so this retries. The web server stays up meanwhile.
    def seedAdmin(self, attempts: int = 30, delaySeconds: float = 2):
        s = self.settings
        for _ in range(attempts):
            try:
                self.auth.seedAccount(s.adminUsername, s.adminEmail, s.adminPassword)
                self.files.ensureDefaultFolders(s.adminUsername)
                print("Admin account ready.")
                return
            except Exception as error:
                print(f"Waiting for the databases ({error})...")
                time.sleep(delaySeconds)
        print("Could not seed the admin account; logins will fail until the databases are reachable.")


def buildContainer(settings: Optional[Settings] = None) -> Container:
    s = settings or Settings.fromEnv()

    userManager = UserManager(UserDatabaseAdapter(s.conninfo("user_db")), ScryptPasswordHasher())
    files = FileService(
        PostgresFolderRepository(s.conninfo("indexDB")),
        PostgresFileIndex(s.conninfo("indexDB")),
        MongoContentStore(s.mongoUri, s.mongoDatabase),
    )
    auth = AuthService(
        userManager,
        InMemorySessionStore(s.sessionSeconds),
        SlidingWindowLimiter(s.loginMaxFailures, s.limitWindowSeconds),
        SlidingWindowLimiter(s.registerMaxPerWindow, s.limitWindowSeconds),
        onSignedIn=files.ensureDefaultFolders,  # everyone who signs in has their default folders
    )
    google = GoogleSignIn(
        GoogleIdentityProvider(s.googleClientId, s.googleClientSecret, s.googleDiscoveryUrl),
        InMemoryPendingLogins(STATE_SECONDS),
        s.googleRedirectUri,
    )
    return Container(s, auth, files, google)
