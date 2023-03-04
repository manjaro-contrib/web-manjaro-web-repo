#!/usr/bin/env python3

import json
import urllib.request
import time
import socket

from collections import OrderedDict
from mirror import Mirror
from builder import Builder
from logger import Logger
from conf import MIRRORS_URL, BRANCHES


class StatusChecker():
    """Launch of actions"""

    def __init__(self):
        self.logger = Logger()
        self.mirrors = list()
        self.hashes = list()
        self.states = list()
        self.countries = list()
        self.logger.info("manjaro-web-repo is starting")

    def get_mirrors(self):
        """Get list of mirrors"""
        try:
            with urllib.request.urlopen(MIRRORS_URL, timeout=10) as mirrors_file:
                self.mirrors = json.loads(mirrors_file.read().decode("utf-8"),
                                          object_pairs_hook=OrderedDict)
        except (urllib.error.URLError, socket.timeout) as e:
            self.logger.error("can't fetch list of mirrors", e)

    def get_hashes(self):
        """Get last hashes"""
        for branch in BRANCHES:
            try:
                with open("/var/repo/repo/" + branch + "/state", "r") as branch_state:
                    content = branch_state.read()
                    pos = content.find("state=")
                    if pos >= 0:
                        self.hashes.append(content[pos + 6:pos + 46])
            except OSError:
                pass
        if len(self.hashes) < len(BRANCHES):
            self.logger.error("can't fetch last hashes")

    def check_mirrors(self):
        """Check each mirror"""
        nb = len(self.mirrors)
        for i, mirror in enumerate(self.mirrors):
            print("({}/{}): {}".format(i + 1, nb, mirror["url"]))
            mirror = Mirror(mirror)
            if not mirror.country in self.countries:
                self.countries.append(mirror.country)
            mirror.get_state_file()
            mirror.read_state_file(self.hashes)
            mirror_status = {
                "url": mirror.url,
                "protocols": mirror.protocols,
                "country": mirror.country,
                "last_sync": mirror.last_sync,
                "branches": mirror.branches
            }
            self.states.append(mirror_status)
        self.logger.info("{} mirror(s) added".format(len(self.states)))

if __name__ == "__main__":
    status_checker = StatusChecker()
    status_checker.get_mirrors()
    status_checker.get_hashes()
    status_checker.check_mirrors()
    builder = Builder(status_checker.states, status_checker.countries)
    builder.generate_output()
    status_checker.logger.close()
