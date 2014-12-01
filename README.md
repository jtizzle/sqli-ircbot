sqli-ircbot
===========

multi-server ircbot that works with the sqlmap API for security auditing
Features
---------
*multi server and multi channel
*markovian AI chaining
*sqlmap scanning
*btc rates
*md5 and sha1 password cracking from web based API

####requires beautifulsoup4 and requests python3 packages

***
For sqlmap features to work, you must be running sqlmapapi.py from the sqlmap package
here https://github.com/sqlmapproject/sqlmap/tarball/master

It can be run on remote server or on localhost. by defualt it is configured to run through tor in modules/sqlmap.py
with the setting "tor": true in the data dictionary variable. If you don't plan on scanning through the tor network,
change the all the settings to "tor": false
***
