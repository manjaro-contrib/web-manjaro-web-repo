import json

files = ["mirrors.json", "mirrors.offline.json", "mirrors.outdated.json"]


def sort_key(mirror):
    return mirror["country"].casefold(), mirror["url"].casefold()


for name in files:
    with open(name, encoding="utf-8") as f:
        mirrors = json.load(f)

    mirrors.sort(key=sort_key)

    with open(name, "w", encoding="utf-8") as f:
        json.dump(mirrors, f, indent=4, ensure_ascii=False)
        f.write("\n")

    print(f"{name}: sorted {len(mirrors)} entries")
