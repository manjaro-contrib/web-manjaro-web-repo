#!/usr/bin/env python3

import json
import urllib.request
import datetime
import socket

from logger import Logger
from conf import BRANCHES


class Mirror():
    """Handle all mirror's properties"""

    def __init__(self, mirror):
        self.logger = Logger()
        self.state_file = None
        self.url = mirror["url"]
        self.country = mirror["country"]
        self.protocols = mirror["protocols"]
        self.last_sync = str()
        self.branches = list()

    def get_state_file(self):
        """Fetch state file"""
        try:
            with urllib.request.urlopen(self.url + "state", timeout=10) as state_file:
                self.state_file = state_file.read().decode("utf-8")
        except (urllib.error.URLError, socket.timeout) as e:
            self.logger.error("{}: can't read state file".format(self.url), e, False)
        except urllib.error.HTTPError as e:
            self.logger.error(e)

    def read_state_file(self, hashes):
        """Read infos from state file"""
        if self.state_file:
            mirror_date = self.state_file.split("date=", 1)[1]
            mirror_date = datetime.datetime.strptime(mirror_date, "%Y-%m-%dT%H:%M:%SZ")
            seconds = (datetime.datetime.utcnow() - mirror_date).total_seconds()
            minutes = seconds // 60
            elapsed_hours = str(int(minutes // 60)).zfill(2)
            elapsed_minutes = str(int(minutes % 60)).zfill(2)
            self.last_sync = "{}:{}".format(elapsed_hours, elapsed_minutes)
            for i, branch in enumerate(BRANCHES):
                url = self.url + branch + "/state"
                try:
                    with urllib.request.urlopen(url, timeout=10) as state_file:
                        state_file = state_file.read().decode("utf-8")
                        branch_hash = state_file.split("state=", 1)[1].split('\n')[0]
                        self.branches.append(int(branch_hash == hashes[i]))
                except (urllib.error.URLError, socket.timeout) as e:
                    self.logger.error("{}: can't read hash from state file".format(url), e, False)
        if not self.last_sync:
            self.last_sync = -1
        if len(self.branches) < 3:
            self.branches = [-1, -1, -1]
