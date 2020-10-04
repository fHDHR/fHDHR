import os
import sys
import urllib.request
import json
import datetime


def clean_exit():
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(0)


class Locast_Auth():
    login_token = None

    def __init__(self, config):
        self.config = config.copy()

        # attempt login
        if not self.login():
            print("Invalid Locast Login Credentials. Exiting...")
            clean_exit()

        # check donate status
        if not self.validate_user():
            clean_exit()

    def check_token(self):
        if not self.token:
            self.login()
            if not self.login():
                print("Invalid Locast Login Credentials. Exiting...")
                clean_exit()
            # check donate status
            if not self.validate_user():
                clean_exit()

    def login(self):
        # login
        print("Logging into Locast using username " + self.config["proxy"]["username"] + "...")

        loginReq = urllib.request.Request('https://api.locastnet.org/api/user/login',
                                          ('{"username":"' + self.config["proxy"]["username"] +
                                              '","password":"' + self.config["proxy"]["password"] +
                                              '"}').encode("utf-8"),
                                          {'Content-Type': 'application/json'})

        loginOpn = urllib.request.urlopen(loginReq)
        loginRes = json.load(loginOpn)
        loginOpn.close()

        self.token = loginRes["token"]
        return True

    def validate_user(self):
        print("Validating User Info...")

        # get user info and make sure we donated
        userReq = urllib.request.Request('https://api.locastnet.org/api/user/me',
                                         headers={'Content-Type': 'application/json',
                                                  'authorization': 'Bearer ' + self.token})

        userOpn = urllib.request.urlopen(userReq)
        userRes = json.load(userOpn)
        userOpn.close()

        print("User Info obtained.")
        print("User didDonate: {}".format(userRes['didDonate']))
        # Check if the user has donated, and we got an actual expiration date.
        if userRes['didDonate'] and userRes['donationExpire']:
            # Check if donation has expired.
            donateExp = datetime.datetime.fromtimestamp(userRes['donationExpire'] / 1000)
            print("User donationExpire: {}".format(donateExp))
            if datetime.datetime.now() > donateExp:
                print("Error!  User's donation ad-free period has expired.")
                return False
        else:
            print("Error!  User must donate for this to work.")
            return False

        return True
