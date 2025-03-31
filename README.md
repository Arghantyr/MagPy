# Introduction
MagPy is a Docker-based stack for managing data retrieval, manipulation and visualisation.

# How it works?
MagPy was created as means to automatically archive content created on WorldAnvil.com, so it comes with a backbone of treating every object as having a Universal Unique Identifier (UUID). To facilitate change tracking, `hash_reg` dictionary is used. In its simplest form it comprises of `UUID: SHA1(JSONStringObject)` key-pair entries. Whenever the current value of SHA1() differs for the given UUID, the object is saved and commited for push to the remote repository and the `hash_reg` is updated with the new value.

To lower the server load, MagPy will use the lower output "beacon" API calls to find out if the object has changed. Only then, will it follow up with a "full" API call to retrieve the changed object and calculate the SHA1() hash.
## Prerequisites
1. Valid RSA-type identification private key named `id_rsa` connected to the GitHub account. This is placed inside the `gitworker/.ssh` directory, from which it is added to the `ssh-agent` when `initiate-gitworker.sh` script is run.
2. `gitworker.py` script, which will:
    - retrieve an object with a diistinct UUID
    - calculate a SHA1 hash of the JSONString of the object
    - compare the SHA1 hash to that stored in `hash_reg`
    - in the event of difference between SHA1 hashes:
        - the object will be saved to gitworker/repo/<remote repo name>/<UUID> file
        - the new SHA1 hash will replace the existing SHA1 hash for that particular UUID
        - the modified <UUID> file will be `git push`-ed to the remote GitHub repository

# Changelog
## 2025-03-25
- Feature: data is `git push`-ed to remote GitHub repository based on change of the SHA1 hash of the object
- Version 0.1 created
