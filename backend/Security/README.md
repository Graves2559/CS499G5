# Grouping of Requirements:
1. Identity and Credentials: (RQ1, RQ2, RQ11): {Bound Email; No Google Login; Password hashing}
        (TODO: RQ1, RQ2)

2. Password Recovery: (RQ3): {Password Reset via Email}
        (TODO: RQ3)

3. Account Hold and Prevention of Hijacking: (RQ4, RQ10): {Account Hold, Phone Number Replacement}
        (TODO: RQ4, RQ10)

4. Removing Account Hold: (RQ5, RQ6, RQ8, RQ9): {Security Questions, Phone Verification Fallback for Security Questions, Security QnA Hashing, Security Question Reset}
        (TODO: RQ5, RQ6, RQ8, RQ9)

5. Symmetric Key Reset: (RQ13): {Resetting private symmetric key (HelpDesk)}
        (TODO: RQ13)


# Requirements:

## {1. Bound Email}
To be secure, **there must be an email attached to each user**, in case this site's account is compromised. That way, the email can be used to reset it. 

## {2. No Google Login}
To login and bind to an email, we do not need to login through Google. In fact, there will be **no Google login allowed.** This makes the system more reliable, since if the CloudFlare service is not paid, the account creation will still work, as there is no Google login (which requires a fixed IP address from some tunneling service, e.g., CloudFlare).

## {3. Password Reset via Email}
If the site account is compromised, **the bound email will be able to reset the account password**. If the user does **reset their site account's password, then everybody on that account must be logged out to login into said account again**.  If the email is compromised, then there must be some time period to allow for changing the account password (**that is, when you attempt to change your password, it will ask for a verification code**). We assume that the email service allows a route to prevent hackers from hijacking your email and barring you from entering your email.

## {4. Approval of bound email for symmetric key reset}
**Before resetting any symmetric key, the system must require explicit confirmation from the bound email to confirm that the user wants to reset their symmetric key**. 

## {12. Account holds}
In the case that the email and site account is compromised, then 

        Tangential note: if the attacker compromises your site account (and not email) and does a 
            (a) half hold, the solution is the security questions (and if forgotten, then phone verification code). If you lost both, you can still do the phone verification code, though it will take longer. 

            (b) full hold, it is statistically unlikely, due to needing an email confirmation (and phone verification code). The email confirmation MUST have solely a confirm button, rather than accompanying it with a cancel button, due to the case in which there is a compromising in both email and site account.

        HALF HOLD (less secure - Either 2- or 4- phone probation/time limit) (when you have COMPLETELY lost your phone with said phone number)
        (1) The same as (ARCHIVED) FULL HOLD but 
            (a) that changing your phone number is fine. Refer to (RQ10, Case A) for the process of changing your phone number
            (b) that changing your password is fine (but it will not log anyone out)

            If the half hold is lifted, then changing your password will log you out. To lift the half hold, it requires the email and (security QnAs or phone verification code).

            If you can address the compromisal of the account, then they will not be able to lift the half hold. Given that nobody can cancel the probation period, they will be able to get the phone verification code, but not compromise the email again (else, it is a permanent dead end). Then, attempt to change the phone number. If they do it first, you would have to wait again, but they would have to actively go out of their way to keep doing that. So in case they forget, you can immediately do it and get the account back.

        Half hold is done (given that your email and site account are both compromised) when you have COMPLETELY lost your phone with said phone number. You have 2 or 4 weeks to log the person(s) compromising your email out, so that you can log the person(s) compromising your site account out. If not, once the person(s) has changed it to their phone, then they can get the phone verification codes. This means that (if they have access to the email as well) they will be able to unpause the half hold on your account, allowing them to log you out completely.


        [ARCHIVED - NOT VIABLE]
        FULL HOLD (more secure, no time limit) 
        Note: This means that there can never be no time limit, due to the security issue. {Look in (RQ10, Archived: Case B})

        [RQ: There must be an email confirmation AND phone code]
            –> Phone code is done simply due to (1) the case where there is a compromise in both the email and site account, and the person(s) is intent on doing a full hold, and (2) this rule enforces users who have lost their phone associated to said phone number to not be able to do this option.
            –> Note: if the person who does this full hold suddenly loses their phone afterwards during this hold, there is not much leeway.
        (1) there is a button for the user to be place all of their actions on hold,
        (2) explicitly asking 3 times whether they wish to do so, such that 
        (3) any action (including decryption of files, resetting symmetric keys, changing account password, changing bound email, etc.) will not be able to be done. However, even when placed on hold, encrypting files are still fine.
        (4) Accompany said 3 confirmations of said hold button with this: "If you have lost your phone for said phone number, do not this choose option."

## {5. Security Questions}
**Have the user set up some security questions.** When the user wants to **remove the hold on the site account, enter the security questions (up to 10 tries) then enter a verification code sent to their bound email (We assume that the hold is done only AFTER the comprisal of the email is addressed.)** This way, to remove the hold, it doesn't only require a compromised email but something only the user should know.

## {6.Phone Verification Fallback for Security Questions}
**Have the user bind their phone to the account** If the user forgets the security questions, they must use their phone for the verification code. The **phone verification route acts in place of the security questions**, given that the security question is forgotten or the security question's attempts are all used up.  **If over 10 attempts for the security questions (track within DB), it will remove the security questions option and ask for the 6-digit verification code through their phone**. **For the verification code, the user can try up to 5 times. If past 5 times, then have the user request for another 6-digit verification code (We assume the verification code is a moving target, so there will not be a collision between them)**. The moving target works because even if the attacker tries some same number consecutively, it would take in the worst case 1 million tries (including the 0). This means that the probability of meeting that  is 5 / 1 million, or 0.0005%. Over a year of nonstop attacking, given that the attacker uses all 10 attempts of new verification code every day: 50 × 365 / 1,000,000 ≈ 1.8%. (RQ7 applies as well) (RQ5 applies as well [if user matches phone verification code, then ask for email service right after])

        Important reminder: We assume that the hold is unpaused only AFTER the comprisal of the email is addressed.


## {7. Verification Code Limitations / Constraints}
Have it so that **there is always a 60s delay for sending another verification code (email, phone)**. Have it so that **there is an expiry within 10 minutes (email, phone)**. Furthermore, **have it so that after 10 verification codes (email, phone), they can try again in 24 hours (the DB tracks the time duration after 10 verification codes)**. This makes it so that the 0.0005% becomes extremely unlikely to break under some time while the user is trying to address the email compromisal. 

        However, since the attacker burn all of attempts of the the phone verification process, there SHALL be a confirmation in the bound email to do that again at any time during now and the 24 hours later ONLY ONCE. This makes it so that the attacker does not really know when the user will attempt to do it, making the attacker have to constantly watch and refresh the page for the phone verification process to take up.



## {8. Security QnA Hashing}
The security questions and answers must be combined together and then hashed. Repeat this step until all of the questions and answers are hashed. Then concatenate them in a fixed order, where H(security question 1) + H(security question 2) + ... + H(security question k) = H1. Then hash h1, such that H(h1) = h2. (Related: RQ 11)



## {9. Security Question Reset}
To reset the security question, if the security question is remembered, the user must confirm through their email. If the security question is forgotten (**AND that the account is not on hold**), it will ask through the phone verification code to reset it. Else, it cannot be changed.


## {10. Phone Number Replacement}
If the user loses their phone, 

        Case A:  given that the account is not on hold or is on a half hold, to switch to a new phone number, there will be a probation period of 2 weeks or 4 weeks. This should be adequate time to address the email changes. No one can cancel the new phone number during this probation period (due to RQ4, half hold case).

            The 2 week or 4 week is done through a dropdown box.

        (ARCHIVED) 
            Case B: given that the account is on a full hold, that is, you had your phone before and then you placed your account on full hold, and then lost your phone some time afterwwards, then you need your security questions. Else, this is a permanent dead end.
        
                Hence, there are 3 clear and explicit reminders that you should NOT put your account on full hold, UNLESS you are 100% certain of the security questions and will not forget it. The problem is that if the attacker somehow exhausted the max 10 attempts, you must require your (lost) phone, which is nearly impossible. 

            Therefore, Case B is removed, meaning there will never be a full hold.


## {11. Password Hashing}
The password must be hashed. The username doesn't. 

## {13. Resetting private symmetric key}
Refer to (Resetting private symmetric key ("HelpDesk)") from Concept of Operations

# Concept of Operations

## Encryption and Decryption:

### **Assumption**:
1. The user has opted for the choice of encrypting files.

### **Operations**

#### Set-Up
1. The user will be given a symmetric key "x". **This symmetric key will use an envelope technique, where T(x, salt) = y1**
2. The user will click the "encrypt" button. This means that there will be some key "dataKey" that will encrypt and decrypt the file. 

        The AES-GCM cypher relies on the security of the private key "x" hard to break, where "x" is transformed into some tag. 

        Encryption: To do so, the system will 
        (1) Create said "dataKey" and encrypt the file with it (with some nonce).
        (2) Encrypt the "dataKey" via an AES cypher AES(dataKey, y1, nonce) = y2, where y2 = (encrypted dataKey || tag1), and the tag1 is a keyed checksum (MAC) onto the encrypted dataKey (refer to 2a for further details)
        (2a) The AES-GCM library computes tag1 = GHASH(y1, nonce, encrypted dataKey)
        (3) Modify y2, such that y2 <– {y2, nonce}, such that the decryption process can use the nonce later.
        (4) Store the modified y2 into the DB, which acts as an encrypted dataKey and tag (alongside an aid for the decryption, via the nonce)

        Storage: the salt and modified y2 will be stored together with the encrypted file and username. "x" nor "y1" will  be stored anywhere in the DB.

        Decryption: To do so, the system will 
        (1) Ask for "x"  and "salt".
        (2) Create T(x, salt) = y1. The system will use y1 on the cyphertext (in this case, it is y2). 
        (3) Take (a) some file and (b) use the AES-GCM cypher such that AES_split(y2) = "encrypted dataKey" and "tag1".
        (4) Use the AES-GCM cypher such that AES_decrypt(y1, y2) = dataKey_2 and tag2, where y2 is {Encryption(3)};dataKey_2 is in (4a); and tag2 is in (4b)
        (4a) The AES-GCM library computes the keystream = AES_encrypt(y1, nonce || CTR) and plaintext dataKey_2 = (encrypted dataKey) XOR keystream. 
        (4b) The AES-GCM library computes tag2 = GHASH(y1, nonce, encrypted dataKey)
        (5) If "tag1" = "tag2", then the library releases dataKey_2, which allows the system to decrypt the file with dataKey_2. 

    
Public key | Secret key
--- | ---
salt | private symmetric key "x"
nonce | y1 (wrapping key, derived from x + salt)
encrypted dataKey | dataKey (plaintext)
tag (tag1) | 


#### Maintenance
1. Every 180 days, the private symmetric key must change, based on NIST standards. This is a symmetric cypher, so by the birthday problem's bounding, the danger of collision risk only starts to appear after roughly 2³²–2⁴⁸ encryptions under the same key. A journaling app's per-user entry volume (dozens to maybe thousands of entries) is nowhere near that, so re-encrypting every 8 hours or so is unnecessary.

        Storage: Compute the remaining time against the elapsed time for the current symmetric key alongside the user credentials, with a column "Key Duration", such that the column stores the remaining days and hours left. Use UTC for the hours. 



## Resetting private symmetric key ("HelpDesk")

**Requirements**:
1. Using RQ4 up top, ensure that the bound email is used to confirm the resetting of the symmetric key. Applies to **ALL** routes 

**Operations**
1. If the symmetric key "x" changes, then every encrypted file for said user must be changed to reflect the change in "x". To make it easily identifiable, there will be 2 columns: plaintext and cyphertext. That way, an encrypted file will have its contents encrypted in the cyphertext column, with the batch re-encryption being easily done. 
2. To change the symmetric key "x", there shall be 3 possible routes. 

        (1) You know your symmetric key "x", so you can change it.
        (2) You do not know your symmetric key "x", but you used some one-time recovery (master key) code that was given when you changed/reset the symmetric key "x"
        (3) if routes (1) and (2) cannot apply, this means you can only make a new symmetric key "x". This means every previous file that was encrypted will be deleted. 

NOTE: Even if you do change it, it will require the confirmation of your email (TODO)
If route 3 applies, **there must be 3 chances to explicitly warn that the previous encrypted files will be deleted**

