#!/usr/bin/env python3

MIRRORS_URL = "https://repo.manjaro.org/mirrors.json"
BRANCHES = ("stable", "testing", "unstable")
ROOT_FOLDER = "/var/www/manjaro-web-repo/"
OUTPUT_FOLDER = "docs/"
LOGS_FOLDER = "logs/"
REPO_ROOT = "/var/repo/repo/"
HEADERS = {
    "Accept": "text/plain,application/octet-stream,text/html,*/*",
    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0",
    'X-User-Agent': "ManjaroMirrorBot/1.0 (+https://repo.manjaro.org)"
}
