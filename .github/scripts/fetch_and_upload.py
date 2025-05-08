import requests
import base64
import os
import time

USERNAME = "SlowDogged"
REPO = "Akatsuki-RSC"
FILE_PATH = "beatmaps.txt"
BRANCH = "main"
TOKEN = os.getenv("GITHUB_TOKEN")
API_URL = "https://akatsuki.gg/api/v1/beatmaps?p={page}&l=100"
USER_AGENT = {"User-Agent": "Mozilla/5.0 AkatsukiBot/1.0"}

# Step 1: Download current beatmaps.txt
def get_existing_file():
    api_url = f"https://api.github.com/repos/{USERNAME}/{REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json"
    }
    res = requests.get(api_url, headers=headers)
    if res.status_code != 200:
        raise Exception("❌ Could not fetch beatmaps.txt:", res.text)
    content = base64.b64decode(res.json()["content"]).decode()
    sha = res.json()["sha"]
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    return lines, sha

# Step 2: Get max beatmap ID from file
def get_max_existing_id(lines):
    ids = [int(line.split(",")[0]) for line in lines if "," in line]
    return max(ids) if ids else 0

# Step 3: Fetch only newer beatmaps
def fetch_new_beatmaps(since_id):
    page = 1
    new_beatmaps = []
    while True:
        url = API_URL.format(page=page)
        try:
            res = requests.get(url, headers=USER_AGENT, timeout=10)
        except Exception as e:
            print(f"⚠️ Request failed on page {page}:", e)
            break

        if res.status_code != 200:
            print("❌ Failed to fetch page:", res.text)
            break

        beatmaps = res.json().get("beatmaps", [])
        if not beatmaps:
            break

        page_new = []
        for b in beatmaps:
            bid = int(b["beatmap_id"])
            ranked = int(b["ranked"])
            if bid <= since_id:
                print(f"🛑 Stopped at beatmap ID {bid} (already known)")
                return new_beatmaps
            page_new.append((bid, ranked))

        new_beatmaps.extend(page_new)
        print(f"📄 Page {page}: +{len(page_new)} new beatmaps")
        page += 1
        time.sleep(0.5)

        if len(beatmaps) < 100:
            break

    return new_beatmaps

# Step 4: Upload updated file to GitHub
def upload_file(all_lines, sha):
    sorted_lines = sorted(set(all_lines), key=lambda x: int(x.split(",")[0]))
    content_str = "\n".join(sorted_lines) + "\n"
    encoded = base64.b64encode(content_str.encode()).decode()

    api_url = f"https://api.github.com/repos/{USERNAME}/{REPO}/contents/{FILE_PATH}"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json"
    }

    data = {
        "message": f"Auto-update beatmaps.txt with only new beatmaps",
        "content": encoded,
        "branch": BRANCH,
        "sha": sha
    }

    res = requests.put(api_url, headers=headers, json=data)
    if res.status_code in (200, 201):
        print(f"✅ Uploaded {len(all_lines)} total lines to beatmaps.txt")
    else:
        print("❌ Upload failed:", res.text)

# Main logic
def main():
    print("🔁 Checking for new beatmaps...")
    lines, sha = get_existing_file()
    max_id = get_max_existing_id(lines)
    print(f"📁 Existing max beatmap ID: {max_id}")

    new_maps = fetch_new_beatmaps(max_id)
    if new_maps:
        print(f"➕ Found {len(new_maps)} new beatmaps.")
        combined = lines + [f"{bid}, {ranked}" for bid, ranked in new_maps]
        upload_file(combined, sha)
    else:
        print("🟢 No new beatmaps found.")

if __name__ == "__main__":
    main()
