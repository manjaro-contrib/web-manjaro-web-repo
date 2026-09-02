import json
import requests
import datetime

"""
This file loads the the status.json file from the mirror endpoint 
and updates the mirrors.json and mirrors.outdated.json files
Mirrors which are either not reachable or not up to date are moved into mirrors.outdated.json
"""

endpoint = "https://mirrors.manjaro.org/status.json"
json_path_mirrors = "mirrors.json"
json_path_outdated = "mirrors.outdated.json"


def house_keeping(url: str, mirrors_ok_file: str, mirrors_outdated_file: str):
    mirrors_ok = []
    with open(mirrors_outdated_file, "r") as current_mirrors_outdated:
        mirrors_outdated = json.load(current_mirrors_outdated)
    try:
        response = requests.get(f"{url}", headers={'User-Agent': 'mirror-house-keeping'})
        mirror_status = response.json()
        for mirror in mirror_status:
            if mirror["branches"] == [-1, -1, -1] or mirror["last_sync"] == -1:
                print("Moving mirror:", mirror["url"], "into mirrors.outdated.json")
                mirrors_outdated.append({
                    "removed": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "country": mirror["country"],
                    "url": mirror["url"],
                    "protocols": mirror["protocols"]
                })
                continue
            mirrors_ok.append({
                "country": mirror["country"],
                "url": mirror["url"],
                "protocols": mirror["protocols"]
            })
        # write the new mirrors.json
        with open(mirrors_ok_file, "w") as json_output:
            json.dump(mirrors_ok, json_output, sort_keys=True)
        # write the new mirrors.outdated.json
        with open(mirrors_outdated_file, "w") as json_output:
            json.dump(mirrors_outdated, json_output, sort_keys=True)
    except Exception as e:
        print(f"{url}: could not read status file", e)
        exit(1)


if __name__ == "__main__":
    house_keeping(endpoint, json_path_mirrors, json_path_outdated)
