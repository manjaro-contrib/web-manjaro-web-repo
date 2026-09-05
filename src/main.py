#!/usr/bin/env python3
import sys
import fcntl
import json
import socket
import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from collections import OrderedDict

import logger
from mirror import Mirror
from builder import Builder
from logger import Logger
from conf import MIRRORS_URL, BRANCHES, HEADERS, REPO_ROOT, GLOBAL_TIMEOUT, MIRROR_GRACE_PERIOD

socket.setdefaulttimeout(GLOBAL_TIMEOUT)

def acquire_lock(lock_path="/tmp/manjaro-web-repo.lock"):
    lock_file = open(lock_path, "w")
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return lock_file
    except BlockingIOError:
        logger = Logger()
        logger.info("Another instance of manjaro-web-repo is already running. Exiting.")
        sys.exit(0)


class StatusChecker:
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
        req = Request(MIRRORS_URL)
        req.headers = HEADERS
        try:
            with urlopen(req) as mirrors_file:
                self.mirrors = json.loads(mirrors_file.read().decode("utf-8"),
                                          object_pairs_hook=OrderedDict)
        except (HTTPError, URLError, socket.timeout) as e:
            self.logger.error("can't fetch list of mirrors", e)

    def get_master_hashes(self):
        """Get last hashes"""
        for branch in BRANCHES:
            try:
                with open(REPO_ROOT + branch + "/state", "r") as branch_state:
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
        self.mirrors.sort(key=lambda x: x["country"])
        nb = len(self.mirrors)
        for i, mirror in enumerate(self.mirrors):
            print("({}/{}): {}".format(i + 1, nb, mirror["url"]))
            mirror = Mirror(mirror)
            if mirror.country not in self.countries:
                self.countries.append(mirror.country)
            if not mirror.get_global_state_file():
                continue
            mirror.read_state_file(self.hashes)
            if mirror.last_sync_age > MIRROR_GRACE_PERIOD:
                self.logger.info(f"Skipping mirror {mirror.url} (last sync age: {mirror.last_sync_age} hours)")
                continue
            mirror_status = {
                "url": mirror.url,
                "protocols": mirror.protocols,
                "country": mirror.country,
                "last_sync": mirror.last_sync,
                "branches": mirror.branches
            }
            self.states.append(mirror_status)
        self.logger.info("{} mirror(s) checked".format(len(self.states)))


if __name__ == "__main__":
    _lock = acquire_lock()
    status_checker = StatusChecker()
    begin = datetime.datetime.now()
    status_checker.get_mirrors()
    status_checker.get_master_hashes()
    status_checker.check_mirrors()
    builder = Builder(status_checker.states, status_checker.countries)
    builder.generate_output()
    status_checker.logger.info("Time spent {}".format(datetime.datetime.now() - begin))
    status_checker.logger.close()
