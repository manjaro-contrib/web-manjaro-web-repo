#!/usr/bin/env python3
import socket
import datetime

from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from logger import Logger
from conf import BRANCHES, UA


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
            with urlopen(
                Request(f"{self.url}state", headers={'User-Agent': UA}), timeout=10
                ) as state_file:
                self.state_file = state_file.read().decode("utf-8")
        except (URLError, socket.timeout, HTTPError) as e:
            self.logger.error(f"{self.url}: can't read state file", e, False)

    def read_state_file(self, hashes):
        """Read infos from state file"""
        if self.state_file:
            mirror_date = self.state_file.split("date=", 1)[1]
            mirror_date = datetime.datetime.strptime(mirror_date, "%Y-%m-%dT%H:%M:%SZ")
            seconds = (datetime.datetime.utcnow() - mirror_date).total_seconds()
            minutes = seconds // 60
            elapsed_hours = str(int(minutes // 60)).zfill(2)
            elapsed_minutes = str(int(minutes % 60)).zfill(2)
            self.last_sync = f"{elapsed_hours}:{elapsed_minutes}"
            for i, branch in enumerate(BRANCHES):
                url = f"{self.url}{branch}/state"
                try:
                    with urlopen(url, timeout=10) as state_file:
                        state_file = state_file.read().decode("utf-8")
                        branch_hash = state_file.split("state=", 1)[1].split('\n')[0]
                        self.branches.append(int(branch_hash == hashes[i]))
                except (URLError, socket.timeout, HTTPError) as e:
                    self.logger.error(f"{url}: can't read hash from state file", e, False)
        if not self.last_sync:
            self.last_sync = -1
        if len(self.branches) < 3:
            self.branches = [-1, -1, -1]
