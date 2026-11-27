
'''
EmailService.py

'''


class EmailService():
    def __init__(self, email: str):
        self.email = email
    
    def sendVerificationCode(self):
        # Implementation for sending a verification email goes here
        pass

    def validateEmail(self) -> bool:
        # Implementation for validating the email format goes here
        return "@" in self.email and "." in self.email
    


