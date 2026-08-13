import json
from collections import defaultdict

files = ["mirrors.json", "mirrors.offline.json", "mirrors.outdated.json"]


def sort_key(mirror):
    return mirror["country"].casefold(), mirror["url"].casefold()


def split_url(url):
    """Split a url into (scheme, rest), both casefolded for comparison."""
    scheme, sep, rest = url.partition("://")
    if not sep:
        return "", url.casefold()
    return scheme.casefold(), rest.casefold()


def describe(mirror):
    return f"{mirror['url']} [{mirror['country']}, {'/'.join(mirror.get('protocols', []))}]"


def dedupe(name, mirrors):
    """Drop entries whose url is already present, preferring https over http.

    Entries are grouped by their url with the scheme stripped, so
    http://host/manjaro/ and https://host/manjaro/ count as one mirror.
    """
    groups = defaultdict(list)
    for mirror in mirrors:
        groups[split_url(mirror["url"])[1]].append(mirror)

    def keeper_rank(item):
        index, mirror = item
        # https first, then the entry listing the most protocols, then file order
        return split_url(mirror["url"])[0] != "https", -len(mirror.get("protocols", [])), index

    dropped = set()
    for rest, entries in groups.items():
        if len(entries) == 1:
            continue

        keeper = min(enumerate(entries), key=keeper_rank)[1]
        print(f"{name}: duplicate url {rest}")
        print(f"    keep    {describe(keeper)}")
        for mirror in entries:
            if mirror is keeper:
                continue
            dropped.add(id(mirror))
            print(f"    discard {describe(mirror)}")
            if mirror["country"] != keeper["country"]:
                print(f"        note: country differs ({mirror['country']} vs {keeper['country']})")
            lost = set(mirror.get("protocols", [])) - set(keeper.get("protocols", []))
            if lost:
                print(f"        note: protocols only listed on the discarded entry: {sorted(lost)}")

    return [m for m in mirrors if id(m) not in dropped], len(dropped)


for name in files:
    with open(name, encoding="utf-8") as f:
        mirrors = json.load(f)

    mirrors, removed = dedupe(name, mirrors)
    mirrors.sort(key=sort_key)

    with open(name, "w", encoding="utf-8") as f:
        json.dump(mirrors, f, indent=4, ensure_ascii=False)
        f.write("\n")

    summary = f"{name}: sorted {len(mirrors)} entries"
    if removed:
        summary += f", removed {removed} duplicate(s)"
    print(summary)
