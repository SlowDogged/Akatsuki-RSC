import requests
import base64
import os
import time

USERNAME = "SlowDogged"
REPO = "Akatsuki-RSC"
FILE_PATH = "beatmaps.txt"
BRANCH = "main"
TOKEN = os.getenv("GITHUB_TOKEN")

HEADERS = {
    "User-Agent": "Mozilla/5.0 AkatsukiBot/1.0"
}

def fetch_all_beatmaps():
    page = 1
    result = []
    while True:
        url = f"https://akatsuki.gg/api/v1/beatmaps?p={page}&l=100"
        try:
            res = requests.get(url, headers=HEADERS, timeout=10)
        except Exception as e:
            print(f"⚠️ Request failed on page {page}:", e)
            break

        if res.status_code != 200:
            print("Failed to fetch page:", res.text)
            break

        data = res.json().get("beatmaps", [])
        if not data:
            break

        result.extend((str(b["beatmap_id"]), str(b["ranked"])) for b in data)
        print(f"📄 Page {page}: +{len(data)} beatmaps")
        page += 1
        time.sleep(1)  # <- Delay between requests to avoid Cloudflare

        if len(data) < 100:
            break

    return result

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
        "message": f"Auto-update beatmaps.txt with new beatmaps",
        "content": encoded_content,
        "branch": BRANCH,
        "sha": sha
    }

    res = requests.put(api_url, headers=headers, json=data)
    if res.status_code in (200, 201):
        print("✅ Updated beatmaps.txt")
    else:
        print("❌ Update failed:", res.status_code, res.text)

def main():
    print("🔄 Fetching latest beatmaps from API...")
    new_beatmaps = fetch_all_beatmaps()
    new_lines = set(f"{bid}, {ranked}" for bid, ranked in new_beatmaps)

    print(f"🗂️  Fetched {len(new_lines)} beatmaps from API.")
    existing_lines, sha = get_existing_file()
    print(f"📁 Existing lines in beatmaps.txt: {len(existing_lines)}")

    # Debug: Print max beatmap ID from both
    try:
        max_existing = max(int(line.split(",")[0]) for line in existing_lines)
        max_new = max(int(line.split(",")[0]) for line in new_lines)
        print(f"📊 Max ID in existing file: {max_existing}")
        print(f"📊 Max ID from API:        {max_new}")
    except Exception as e:
        print("⚠️  Error getting max ID:", e)

    new_only = new_lines - existing_lines
    print(f"➕ New beatmaps to add: {len(new_only)}")

    if new_only:
        print("🆕 Example new entries:")
        for line in sorted(new_only, key=lambda x: int(x.split(",")[0]))[:10]:
            print("   ➤", line)
        combined = existing_lines | new_only
        upload_updated_file(combined, sha)
    else:
        print("🟢 No new beatmaps to update.")

if __name__ == "__main__":
    main()
