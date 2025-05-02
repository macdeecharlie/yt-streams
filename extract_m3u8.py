import os
import subprocess
import hashlib

STREAM_FILE = "streams.txt"
STATIC_STREAMS_FILE = "static_streams.txt"
PLAYLIST_FILE = "playlist.m3u8"
HASH_FILE = "playlist.hash"
REPO_DIR = os.getcwd()
GIT_REMOTE = "origin"
GIT_BRANCH = "main"

def get_streams():
    with open(STREAM_FILE, "r", encoding="utf-8") as f:
        lines = f.read().strip().splitlines()
    return {line.split()[0]: line.split()[1] for line in lines if line.strip()}

def extract_m3u8(url):
    try:
        result = subprocess.run(
            ["yt-dlp", "-g", url],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception as e:
        print(f"Error extracting m3u8 for URL {url}: {e}")
    return None

def sha256sum(text):
    return hashlib.sha256(text.encode()).hexdigest()

def generate_master_playlist(youtube_streams):
    content = "#EXTM3U\n\n"
    for name, url in youtube_streams.items():
        content += f"#EXTINF:-1,{name} - YouTube Live\n{url}\n\n"

    try:
        with open(STATIC_STREAMS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    name, url = line.strip().split()
                    content += f"#EXTINF:-1,{name} - Static Stream\n{url}\n\n"
    except Exception as e:
        print(f"Error reading static streams: {e}")

    return content

def playlist_has_changed(new_content):
    new_hash = sha256sum(new_content)
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, "r") as f:
            old_hash = f.read().strip()
        if new_hash == old_hash:
            return False  # no change
    with open(HASH_FILE, "w") as f:
        f.write(new_hash)
    return True

def write_playlist(content):
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
        f.write(content)

def git_commit_and_push():
    subprocess.run(["git", "add", "."], cwd=REPO_DIR)
    subprocess.run(["git", "commit", "-m", "Auto update playlist with direct m3u8 links"], cwd=REPO_DIR)
    subprocess.run(["git", "push", GIT_REMOTE, GIT_BRANCH], cwd=REPO_DIR)

def main():
    current_streams = get_streams()
    youtube_streams = {}

    for name, url in current_streams.items():
        new_link = extract_m3u8(url)
        if new_link:
            youtube_streams[name] = new_link

    playlist_content = generate_master_playlist(youtube_streams)

    if playlist_has_changed(playlist_content):
        write_playlist(playlist_content)
        git_commit_and_push()
        print("Playlist updated and pushed to GitHub.")
    else:
        print("No changes detected. Skipping git commit and push.")

if __name__ == "__main__":
    main()
