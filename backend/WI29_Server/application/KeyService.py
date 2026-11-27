'''
KeyService.py

Use cases for a user's symmetric-key lifecycle: security questions and the 3 HelpDesk cases for resetting
the passphrase when it's lost. Composes UserLogin's Accounts port (security questions) with the
SymmetricKeyVault port (Security's EncryptionManager) -- this is the one place in WI29_Server allowed to
depend on both, since Case 1 (RQ5/RQ8) gates a reset behind the user's own security-question answers, which
belong to accounts, not encryption.

RQ4: every reset case below requires a confirmation code from requestResetConfirmation -- emailing that code
to the user's bound email is the interface layer's job (it already reaches the user's email through
Accounts.getUser). generateRecoveryCode is NOT gated this way: it only adds a backup envelope while the
passphrase is still known, it does not reset anything.
'''
from typing import Optional

from CommonErrors.Errors import UnauthorizedError
from WI29_Server.application.Ports import Account, Accounts, SymmetricKeyVault


class KeyService:
    def __init__(self, accounts: Accounts, vault: SymmetricKeyVault):
        self.accounts = accounts
        self.vault = vault

    def requestResetConfirmation(self, username: str) -> str:
        return self.vault.requestResetConfirmation(username)

    def setupSecurityQuestions(self, user: Account, questionAnswers: dict):
        self.accounts.setupSecurityQuestions(user, questionAnswers)

    # Case 1: the user still knows their current passphrase.
    def changePassphrase(self, user: Account, confirmationCode: str, oldPassphrase: str, newPassphrase: str,
                          candidateAnswers: Optional[dict] = None):
        self._requireSecurityAnswers(user, candidateAnswers)
        self.vault.changePassphrase(user.getUsername(), confirmationCode, oldPassphrase, newPassphrase)

    def generateRecoveryCode(self, user: Account, passphrase: str) -> str:
        return self.vault.generateRecoveryCode(user.getUsername(), passphrase)

    # Case 2: the passphrase is lost, but the one-time recovery code is available.
    def recoverWithRecoveryCode(self, user: Account, confirmationCode: str, recoveryCode: str, newPassphrase: str):
        self.vault.recoverWithRecoveryCode(user.getUsername(), confirmationCode, recoveryCode, newPassphrase)

    # Case 3 (last resort): both the passphrase and the recovery code are lost. Returns the new one-time
    # recovery code to show once. Every file this user ever encrypted becomes permanently unrecoverable the
    # moment this runs (its dataKey is gone) -- this app has no file-deletion feature yet to also remove the
    # now-garbage ciphertext itself, so it is left in place, inert and undecryptable.
    def wipeAndReprovision(self, user: Account, confirmationCode: str, newPassphrase: str) -> str:
        _, recoveryCode = self.vault.wipeAndReprovision(user.getUsername(), confirmationCode, newPassphrase)
        return recoveryCode

    def _requireSecurityAnswers(self, user: Account, candidateAnswers: Optional[dict]):
        if not self.accounts.verifySecurityAnswers(user, candidateAnswers or {}):
            raise UnauthorizedError("Security question answers are incorrect.")
