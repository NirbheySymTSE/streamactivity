# Track Stream Activity
This script automates the process of tracking user activity in a stream. 

It takes in a configuration file, authentication keys, a service account on the pod, and a streamID. The script takes an optional 'since' argument (epoch timestamp) to search within a given timeframe. The script by default searches the last 7 days of stream activity.

This script uses Python to function, please install it before attempting to run this.

### Install Symphony Python BDK

You will need to install the Python BDK:
```
pip install symphony-bdk-python
```

### Setup config.yaml and RSA
Next, you will be required to have the following:

* RSA Key Pair
* config.yaml
  
These are required for script to authenticate and execute.

**RSA Key Pair**

This may need to come internally from a team who administers your Pod. You can find instructions to create an RSA Key Pair here: https://docs.developers.symphony.com/building-bots-on-symphony/authentication/rsa-authentication#1.-create-an-rsa-key-pair

**config.yaml**

This will be required in this format:

```
host: YOUR-POD-SUBDOMAIN.symphony.com         # your own pod host name

bot:
    username: BOT-USERNAME                    # your service account username
    privateKey:
      path: /path/to/bot/rsa-private-key.pem  # your bot RSA private key
```
For more detailed documentation about BDK configuration, go to: 
https://symphony-bdk-python.finos.org/markdown/configuration.html


### Running the script
Run the script with the following command in your working directory:
```
python streamactivity.py --config /path/to/config.yaml --stream "stream_id"
```

To set a specific timeframe, use this argument:
```
python streamactivity.py --config /path/to/config.yaml --since epoch_timestamp --stream "stream_id"
```

### Setup logging and debug
Setting up and enabling logging is not necessary to run this script but can be useful for debugging. 

Uncomment lines 13-15 and create the following file and subdirectory within your working directory:
```
/resources/logging.conf
```

Sample logging.conf:
```
# Sample configuration for logging, prints to the console and to bdk.log file
# See https://docs.python.org/3/library/logging.config.html#logging-config-fileformat

[loggers]
keys=root

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=DEBUG
handlers=consoleHandler,fileHandler

[handler_consoleHandler]
class=StreamHandler
level=DEBUG
formatter=simpleFormatter
args=(sys.stdout,)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s

[handler_fileHandler]
# Rotating log file if size exceeds 10MB
class=logging.handlers.RotatingFileHandler
level=DEBUG
formatter=simpleFormatter
args=('bdk.log', 'w', 10000000, 10)
```
