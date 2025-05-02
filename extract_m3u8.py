import os
import subprocess
import hashlib

STREAM_FILE = "streams.txt"
STATIC_STREAMS_FILE = "static_streams.txt"
M3U8_DIR = "m3u8"
PLAYLIST_FILE = "playlist.m3u8"
REPO_DIR = os.getcwd()
GIT_REMOTE = "origin"
GIT_BRANCH = "main"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/macdeecharlie/yt-streams/main/m3u8"

os.makedirs(M3U8_DIR, exist_ok=True)

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
        print(f"Error extracting: {e}")
    return None

def sha256sum(text):
    return hashlib.sha256(text.encode()).hexdigest()

def write_m3u8(name, url):
    content = f"#EXTM3U\n#EXTINF:-1,{name}\n{url}"
    with open(os.path.join(M3U8_DIR, f"{name}.m3u8"), "w", encoding="utf-8") as f:
        f.write(content)

def write_static_m3u8(name, url):
    """Write static stream m3u8 file in the m3u8 directory."""
    content = f"#EXTM3U\n#EXTINF:-1,{name}\n{url}"
    with open(os.path.join(M3U8_DIR, f"{name}.m3u8"), "w", encoding="utf-8") as f:
        f.write(content)

def read_existing_names():
    return {f.split(".")[0] for f in os.listdir(M3U8_DIR) if f.endswith(".m3u8")}

def generate_master_playlist():
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as playlist:
        playlist.write("#EXTM3U\n\n")
        # Add YouTube streams
        for filename in sorted(os.listdir(M3U8_DIR)):
            if filename.endswith(".m3u8"):
                stream_number = filename.replace(".m3u8", "")
                playlist.write(f"#EXTINF:-1,{stream_number} - YouTube Live\n")
                playlist.write(f"{GITHUB_RAW_BASE}/{filename}\n\n")
        # Append static streams from static_streams.txt
        append_static_streams(playlist)

def append_static_streams(playlist):
    try:
        with open(STATIC_STREAMS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    stream_number, stream_url = line.split()
                    playlist.write(f"#EXTINF:-1,{stream_number} - Static Stream\n")
                    playlist.write(f"{stream_url}\n\n")
                    # Also write the static stream to the m3u8 folder
                    write_static_m3u8(stream_number, stream_url)
    except Exception as e:
        print(f"Error reading static streams: {e}")

def git_commit_and_push():
    subprocess.run(["git", "add", "."], cwd=REPO_DIR)
    subprocess.run(["git", "commit", "-m", "Auto update playlist and m3u8 files"], cwd=REPO_DIR)
    subprocess.run(["git", "push", GIT_REMOTE, GIT_BRANCH], cwd=REPO_DIR)

def main():
    current_streams = get_streams()
    existing_names = read_existing_names()

    # Remove deleted streams
    for old_name in existing_names - current_streams.keys():
        os.remove(os.path.join(M3U8_DIR, f"{old_name}.m3u8"))

    # Update or add new streams
    for name, url in current_streams.items():
        new_link = extract_m3u8(url)
        if new_link:
            m3u8_path = os.path.join(M3U8_DIR, f"{name}.m3u8")
            old_link = ""
            if os.path.exists(m3u8_path):
                with open(m3u8_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if len(lines) >= 3:
                        old_link = lines[2].strip()
            if sha256sum(old_link) != sha256sum(new_link):
                write_m3u8(name, new_link)

    # Always regenerate master playlist
    generate_master_playlist()
    git_commit_and_push()

if __name__ == "__main__":
    main()
