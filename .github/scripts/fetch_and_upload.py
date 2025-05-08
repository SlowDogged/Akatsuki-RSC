import requests
import base64
import os

USERNAME = "your-github-username"  # CHANGE THIS
REPO = "osu-beatmap-status"
FILE_PATH = "beatmaps.txt"
BRANCH = "main"
TOKEN = os.getenv("GITHUB_TOKEN")

# Fetch all pages from Akatsuki API
def fetch_all_beatmaps():
    page = 1
    result = []
    while True:
        url = f"https://akatsuki.gg/api/v1/beatmaps?p={page}&l=100"
        res = requests.get(url)
        if res.status_code != 200:
            print("Failed to fetch:", res.text)
            break
        data = res.json().get("beatmaps", [])
        if not data:
            break
        result.extend((str(b["beatmap_id"]), str(b["ranked"])) for b in data)
        if len(data) < 100:
            break
        page += 1
    return result

# Load current beatmaps.txt from GitHub
def get_existing_file():
    api_url = f"https://api.github.com/repos/{USERNAME}/{REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    res = requests.get(api_url, headers=headers)
    if res.status_code != 200:
        raise Exception("Could not fetch file from GitHub:", res.text)
    content = base64.b64decode(res.json()["content"]).decode()
    sha = res.json()["sha"]
    lines = set(line.strip() for line in content.splitlines() if line.strip())
    return lines, sha

def upload_updated_file(all_lines, sha):
    sorted_lines = sorted(all_lines, key=lambda x: int(x.split(",")[0]))
    final_content = "\n".join(sorted_lines) + "\n"
    encoded_content = base64.b64encode(final_content.encode()).decode()

    api_url = f"https://api.github.com/repos/{USERNAME}/{REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "message": "Auto-update beatmaps.txt from Akatsuki API",
        "content": encoded_content,
        "branch": BRANCH,
        "sha": sha
    }

    res = requests.put(api_url, headers=headers, json=data)
    if res.status_code in (200, 201):
        print("✅ Updated beatmaps.txt")
    else:
        print("❌ Update failed:", res.text)

def main():
    new_beatmaps = fetch_all_beatmaps()
    new_lines = set(f"{bid}, {status}" for bid, status in new_beatmaps)
    existing_lines, sha = get_existing_file()
    all_lines = existing_lines | new_lines
    if all_lines != existing_lines:
        upload_updated_file(all_lines, sha)
    else:
        print("🟢 No new beatmaps to update.")

if __name__ == "__main__":
    main()
