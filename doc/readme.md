# What Is SWBase
SWBase is an Open Source storage and authentication solution for (sex worker friendly) websites that uses OAuth and variable encryption levels for resources. It is written in Python (3.x) and focuses on privacy and security.

**Neither the administrator nor any other users will ever be able to access data marked as private.**

# Technology
SWBase uses multiple technologies to achieve it's goal.

* **Authentication** -- OAuth 2.0
* **Database** -- Redis (for storage of data) and memcached (for storage of oauth2 related data)
* **Web Framework** -- python-flask
* **Encryption** -- 2048 bit RSA encryption keys

# How Does It Work
By default, without any additional setup, SWBase will create a node ```user``` in the database that stores information about the users created. Each entry in the node has four fields: ```username```, ```password```, ```encrypted private key```, ```public key```. The username is stored in plain text, as is the public key. The password is stored as a SHA512 encrypted string. The private key is encrypted using the user's password and a salt, and as such, **if the password is ever lost, any data that is encrypted for that user can not be retrieved**. Changing your own password if possible but only if one is logged in.

SWBase has four "spaces" with differing security levels. They are:
* private
* shared
* protected
* public

## Private
Any data marked as private will be associated with a user and encrypted using that user's public key. They only way to retrieve this data is by using the user's private key, which is stored encrypted (through the user's password and salt) in the database. This means that if a user loses her password, none of this data can be retrieved. Each entry stored privately consists of two fields in the database: The user's id and the encrypted information.

## Shared
Data marked as shared is shared between one or more users. It is encrypted using each party's public key and can thus be read only by those people. The process for encrypting and decryping is a little more complicated here, but in essence it is a simple PGP encryption: Each document is (symmetrically) encrypted using an encrypted key that can only be decrypted by the participants.

1. User **Anna** wants to share something with user **Max** and **Sandra**.
1. Document **Resources** is created and a random key **K<sub>resources</sub>** is generated alongside
2. The document **Resources** is encrypted with the randomly generated key **K<sub>resources</sub>**
3. **Resources** is now stored in the database as it is encrypted.
3. The key **K<sub>resources</sub>** is then encrypted with the public key of each user **Resources** was shared with, creating three new encrypted keys: **E(K<sub>Anna<sub>pub</sub></sub>)<sub>K<sub>resources</sub></sub>**, **E(K<sub>Max<sub>pub</sub></sub>)<sub>K<sub>resources</sub></sub>**, **E(K<sub>Sandra<sub>pub</sub></sub>)<sub>K<sub>resources</sub></sub>**
4. The three generated encrypted keys are then stored in the database alongside the encrypted document **Resources**.
4. The initially generated **K<sub>resources</sub>** is then thrown away as it is no longer needed.

## Protected
Protected data is accessible to anyone logged in to SWBase and is not stored encrypted.

## Public
This data is accessible to anyone, even without being logged in.

# Setup
The setup of SWBase is simple and easy and requires the creation of just one file with instructions on how to map and handle resources. The idea here is that a user and admin does not have to worry about the underlying mechanics of encryption/decryption but can rely on SWBase to handle all these things.

The file is requires a JSON format with instructions for each node (table).

As an example, we create a basic SWBase installation that offers users a personal store for contacts, a shared messaging system and a protected news store and a public announcements store.

Example setup.json
```
{
    "private": {
        "contacts": {
            "name": "string",
            "street": "string",
            "street_number": "number",
            "phone_number": "string",
            "email": "string"
        }
    },
    "shared": {
        "messages": {
            "from": "string",
            "to": ["string"],
            "content": {
                "title": "string",
                "body": "string"
            }
        }
    },
    "protected": {
        "news": {
            "title": "string",
            "body": "string",
            "footer": "string"
        }
    },
    "public": {
        "announcements": {
            "text": "string"
        }
    },
}
```

Possible values for keys are:
* string
* number
* boolean
* {} - to denote an object, or hierarchy
* [] - to denote a list
