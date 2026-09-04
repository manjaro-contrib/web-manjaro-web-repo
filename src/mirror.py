#!/usr/bin/env python3
import socket
import ssl
import datetime

from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

from logger import Logger
from conf import BRANCHES, HEADERS, GLOBAL_TIMEOUT

socket.setdefaulttimeout(GLOBAL_TIMEOUT)

class Mirror:
    """Handle all mirror's properties"""

    def __init__(self, mirror):
        self.logger = Logger()
        self.state_file = None
        self.url = mirror["url"]
        self.country = mirror["country"]
        self.protocols = mirror["protocols"]
        self.last_sync = str()
        self.branches = list()

    @staticmethod
    def _format_network_error(error: Exception) -> str:
        """Classify exceptions into high-signal diagnostic messages."""
        if isinstance(error, HTTPError):
            return f"HTTP {error.code} ({error.reason})"

        if isinstance(error, URLError):
            reason = error.reason
            if isinstance(reason, socket.gaierror):
                return f"Domain vanished / DNS lookup failed: {reason}"
            if isinstance(reason, socket.timeout) or isinstance(reason, TimeoutError):
                return f"Connection timed out: {reason}"
            if isinstance(reason, ConnectionRefusedError):
                return f"Connection refused (server down): {reason}"
            if isinstance(reason, ssl.SSLError):
                return f"SSL/TLS error: {reason}"
            return f"Network URL error: {reason}"

        if isinstance(error, (socket.timeout, TimeoutError)):
            return "Connection timed out"

        return f"Unexpected error: {error}"

    def get_global_state_file(self) -> bool:
        """Fetch state file with granular error logging"""
        try:
            req = Request(f"{self.url}state", headers=HEADERS)
            with urlopen(req) as state_file:
                self.state_file = state_file.read().decode("utf-8")
        except (URLError, socket.timeout, TimeoutError, Exception) as e:
            error_details = self._format_network_error(e)
            self.logger.error(
                f"{self.url}: {error_details}",
                error_details,
                close=False
            )
            return False
        return True

    def read_state_file(self, hashes):
        """Read infos from state file"""
        if self.state_file:
            try:
                date = self.state_file.split("date=", 1)
                if len(date) < 2:
                    self.logger.error(
                        f"{self.url}: global state file is not valid",
                        "date not found",
                        close=False
                    )
                    self.last_sync = -1
                else:
                    mirror_date = self.state_file.split("date=", 1)[1]
                    mirror_date = datetime.datetime.strptime(mirror_date, "%Y-%m-%dT%H:%M:%SZ")
                    now_utc_naive = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
                    seconds = (now_utc_naive - mirror_date).total_seconds()
                    minutes = seconds // 60
                    elapsed_hours = str(int(minutes // 60)).zfill(2)
                    elapsed_minutes = str(int(minutes % 60)).zfill(2)
                    self.last_sync = f"{elapsed_hours}:{elapsed_minutes}"
            except Exception as e:
                self.logger.error(
                    f"{self.url}: global state file is not valid",
                    e,
                    close=False
                )
                self.last_sync = -1

        for i, branch in enumerate(BRANCHES):
            url = f"{self.url}{branch}/state"
            req = Request(url, headers=HEADERS)
            try:
                with urlopen(req) as state_file:
                    state_content = state_file.read().decode("utf-8")
                    branch_hash = state_content.split("state=", 1)[1].split("\n")[0]
                    self.branches.append(int(branch_hash == hashes[i]))
            except (URLError, socket.timeout, TimeoutError, Exception) as e:
                error_details = self._format_network_error(e)
                self.logger.error(
                    f"{url}: can't read branch state file",
                    error_details,
                    close=False
                )
                self.branches.append(-1)

        if not self.last_sync:
            self.last_sync = -1