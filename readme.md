# What Is Nova
Nova is an OpenSource Database solution for websites. It is written in Python (3.x) and focuses on privacy and security. Most importantle Nova allows users to store information securely without an administrator or other person having unfettered access to it. Nova provides a secure storage solution that is easy to use and provides no backdoor for administrators or others to access your data.

# How To Use Nova
Nova is designed to be very easy to use for administrators. It best works in conjunction with nginx, but can be run with any WSGI capable web server. For future easy of use a docker package is planned to make it possible to deploy nova anywhere without any setup. As of now, you will need to set up nova through python, preferably in a virtual environment.

# Security Concerns
Of course there is no absolute security, to think otherwise is folly. However, Nova tries to minimize the leakage of confidential information. As such, it employs RSA encryption of information stored in private nodes and employs SHA512 encryption to protect the keys stored in the database with the user's password and a specific salt for each user. The basic workflow to ensure security is as follows:
1. A user signs up with the password that has been SHA512 encrypted on the client side. This way the plain text password is never sent to the server.
2. Once received, the server takes the client side encrypted password to unlock a user's key. This key is then used to decrypt any sensitive information that is sent back to the user.
3. The user's password is stored encrypted (based on SHA512 and another salt) in the database. This is to ensure that an administrator can not gleam at the database and use a user's client side encrypted password to unlock a key.
4. Once the request is handled the data is thrown away and for another request the user has to supply the password again.
While this means that each request (that requires elevated access) to the server needs to have the password provided, it ensures that the key is only available for a very limited amount of time.
Of course we are talking about Python and as such we do not have a decent way of erasing such memory. However, if you're server's memory is compromised then all the security will probably not be enough to protect your user's data.
