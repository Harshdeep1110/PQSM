import urllib.request, json
url = "https://api.github.com/repos/open-quantum-safe/liboqs/releases/latest"
req = urllib.request.Request(url, headers={"User-Agent": "Python"})
resp = urllib.request.urlopen(req)
data = json.loads(resp.read())
print("Tag:", data["tag_name"])
for asset in data.get("assets", []):
    print("  " + asset["name"] + " (" + str(asset["size"]) + " bytes)")
    print("    " + asset["browser_download_url"])
