'''
KeyRoutes.py

HTTP routes for a signed-in user's symmetric-key encryption (all need the session cookie):
    PATCH /api/me/encryption              {encryptChoice}
    POST  /api/security/questions          {questions}        set up/replace security-question answers
    POST  /api/security/reset/request      RQ4: emails a confirmation code, required by every route below
    POST  /api/security/reset/passphrase   {confirmationCode, oldPassphrase, newPassphrase, securityAnswers?}  (Case 1)
    POST  /api/security/recovery-code      {passphrase}        generates a one-time recovery code (not RQ4-gated)
    POST  /api/security/reset/recover      {confirmationCode, recoveryCode, newPassphrase}                     (Case 2)
    POST  /api/security/reset/wipe         {confirmationCode, newPassphrase}                                   (Case 3, last resort)
    POST  /api/files/rotate-key            {symmetricKey}      re-encrypts every file under a fresh dataKey

Routes only translate HTTP to use-case calls and back; the rules live in the application layer.
'''
from fastapi import APIRouter, Depends

from CommonErrors.Errors import UnauthorizedError
from WI29_Server.application.AuthService import AuthService
from WI29_Server.application.FileService import FileService
from WI29_Server.application.KeyService import KeyService
from WI29_Server.interface.Schemas import (
    ChangePassphraseBody, EncryptChoiceBody, GenerateRecoveryCodeBody, RecoverWithCodeBody, RotateKeyBody,
    SecurityQuestionsBody, WipeAndReprovisionBody,
)
from WI29_Server.interface.Session import makeCurrentUser


def buildKeyRouter(auth: AuthService, keys: KeyService, files: FileService) -> APIRouter:
    router = APIRouter()
    currentUser = makeCurrentUser(auth)

    def currentAccount(username: str):
        user = auth.getUser(username)
        if user is None:
            raise UnauthorizedError("Please sign in.")
        return user

    @router.patch("/api/me/encryption")
    def setEncryptChoice(body: EncryptChoiceBody, username: str = Depends(currentUser)):
        auth.setEncryptChoice(currentAccount(username), body.encryptChoice)
        return {"encryptChoice": body.encryptChoice}

    @router.post("/api/security/questions")
    def setupSecurityQuestions(body: SecurityQuestionsBody, username: str = Depends(currentUser)):
        keys.setupSecurityQuestions(currentAccount(username), body.questions)
        return {"ok": True}

    # RQ4: the code itself is never returned here -- it must reach the user only through their bound email.
    # TODO: this does not send an email yet (no mailer exists anywhere in this app yet -- see
    # UserLogin/domain/EmailService.py); the code is only logged server-side in the meantime.
    @router.post("/api/security/reset/request")
    def requestResetConfirmation(username: str = Depends(currentUser)):
        code = keys.requestResetConfirmation(username)
        print(f"[RQ4] Symmetric-key reset confirmation code for {username}: {code} (email sending not implemented)")
        return {"message": "A confirmation code has been sent to your bound email."}

    @router.post("/api/security/reset/passphrase")
    def changePassphrase(body: ChangePassphraseBody, username: str = Depends(currentUser)):
        keys.changePassphrase(currentAccount(username), body.confirmationCode, body.oldPassphrase,
                              body.newPassphrase, body.securityAnswers)
        return {"ok": True}

    # Not RQ4-gated: the user still knows their passphrase, so this cannot reset anything on its own.
    @router.post("/api/security/recovery-code")
    def generateRecoveryCode(body: GenerateRecoveryCodeBody, username: str = Depends(currentUser)):
        return {"recoveryCode": keys.generateRecoveryCode(currentAccount(username), body.passphrase)}

    @router.post("/api/security/reset/recover")
    def recoverWithRecoveryCode(body: RecoverWithCodeBody, username: str = Depends(currentUser)):
        keys.recoverWithRecoveryCode(currentAccount(username), body.confirmationCode, body.recoveryCode,
                                     body.newPassphrase)
        return {"ok": True}

    @router.post("/api/security/reset/wipe")
    def wipeAndReprovision(body: WipeAndReprovisionBody, username: str = Depends(currentUser)):
        recoveryCode = keys.wipeAndReprovision(currentAccount(username), body.confirmationCode, body.newPassphrase)
        return {"recoveryCode": recoveryCode}

    @router.post("/api/files/rotate-key")
    def rotateEncryptionKey(body: RotateKeyBody, username: str = Depends(currentUser)):
        files.rotateEncryptionKey(username, body.symmetricKey)
        return {"ok": True}

    return router
