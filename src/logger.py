#!/usr/bin/env python3

import datetime
import os

from conf import ROOT_FOLDER, LOGS_FOLDER


class Logger():
    """Handle logs"""

    def __init__(self):
        self.check_folder()
        self.log_path = ROOT_FOLDER + LOGS_FOLDER + "mwr.log"
        self.errors_path = ROOT_FOLDER + LOGS_FOLDER + "errors.log"

    def check_folder(self):
        """Check if logs folder exists"""
        try:
            if not os.path.isdir(ROOT_FOLDER + LOGS_FOLDER):
                os.makedirs(ROOT_FOLDER + LOGS_FOLDER)
        except OSError as e:
            self.error("can't create logs folder", e)

    def info(self, msg):
        """Add line in mwr.log"""
        print(msg.capitalize())
        try:
            with open(self.log_path, "a") as log_file:
                date = datetime.datetime.now().strftime("%c")
                log_file.write("{}: {}\n".format(date, msg))
        except OSError as e:
            self.error("can't write message in log file", e)

    def error(self, msg, exception="", close=True):
        """Add line in errors.log"""
        if exception:
            exception = "-> {}".format(exception)
        self.info(msg)
        try:
            with open(self.errors_path, "a") as errors_file:
                date = datetime.datetime.now().strftime("%c")
                errors_file.write("{}: {} {}\n".format(date, msg, exception))
        except OSError as e:
            self.error("can't write message in errors file", e)
        if close:
            self.close()

    def close(self):
        """Close manjaro-web-repo"""
        self.info("manjaro-web-repo is stopping")
        exit()
