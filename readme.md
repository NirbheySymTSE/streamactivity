# Track Stream Activity
This script will automates the process of tracking user activity in a stream. 

It takes in a configuration file, authentication keys/certs, a service account, and a roomID. Optionally, the script can also take in a 'since' epoch timestamp to search within the given timeframe. The script by default searches 7 days of stream activity.

This script uses Python to function, please install it before attempting to run this.

### Install dependencies and Symphony Python BDK
You will need to install the requirements of the Python BDK (requirements.txt) file.
These can be found here: https://github.com/SymphonyPlatformSolutions/symphony-api-client-python/blob/master/requirements.txt

This file has already been added in this Repository.

To install it, you will need to save it as requirements.txt and install it via the pip command:
```
pip install -r requirements.txt
```

Second, you will need to install the Python SDK:
```
pip install symphony-bdk-python
```

### Setup config.json and RSA
Next, you will be required to have the following:

* RSA Key Pair
* config.yaml
  
These will be required to be passed through to the script so it can be executed.

**RSA Key Pair**

This will need to come internally from your team who administers your Pod.

**config.yaml**

This will be required in this format:

```
host: YOUR-POD-SUBDOMAIN.symphony.com         # your own pod host name

bot:
    username: BOT-USERNAME                    # your bot (or service account) username
    privateKey:
      path: /path/to/bot/rsa-private-key.pem  # your bot RSA private key
```

### Running the script
To execute the script please go to the directory where you have saved the files (RSA keypair, config.json) and run the following command:
```
python add-users-to-room.py --auth "rsa" --config "/path/to/config.json" --csv "/path/to/userIDs.csv" --stream "{streamID}"
```