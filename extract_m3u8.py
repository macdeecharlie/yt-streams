import os
import subprocess
import hashlib

STREAM_FILE = "streams.txt"
STATIC_STREAMS_FILE = "static_streams.txt"
PLAYLIST_FILE = "playlist.m3u8"
M3U8_DIR = "m3u8"
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
        print(f"Error extracting: {e}")
    return None

def sha256sum(text):
    return hashlib.sha256(text.encode()).hexdigest()

def generate_master_playlist(youtube_streams):
    with open(PLAYLIST_FILE, "w", encoding="utf-8") as playlist:
        playlist.write("#EXTM3U\n\n")
        # Write dynamic (YouTube) streams
        for name, url in youtube_streams.items():
            playlist.write(f"#EXTINF:-1,{name} - YouTube Live\n")
            playlist.write(f"{url}\n\n")
        # Append static streams
        append_static_streams(playlist)

def append_static_streams(playlist):
    try:
        with open(STATIC_STREAMS_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    name, url = line.strip().split()
                    playlist.write(f"#EXTINF:-1,{name} - Static Stream\n")
                    playlist.write(f"{url}\n\n")
    except Exception as e:
        print(f"Error reading static streams: {e}")

def update_m3u8_files(youtube_streams):
    # Ensure m3u8 folder exists
    if not os.path.exists(M3U8_DIR):
        os.makedirs(M3U8_DIR)
    
    # Get all current m3u8 file names in the folder
    existing_files = set(os.listdir(M3U8_DIR))

    # Create or update .m3u8 files for the active streams
    for name, url in youtube_streams.items():
        file_name = f"{sha256sum(url)}.m3u8"  # Use a hash of the URL as the filename
        file_path = os.path.join(M3U8_DIR, file_name)

        # Only create/update file if it's not already present
        if file_name not in existing_files:
            with open(file_path, "w", encoding="utf-8") as m3u8_file:
                m3u8_file.write(f"#EXTM3U\n\n#EXTINF:-1,{name} - YouTube Live\n")
                m3u8_file.write(f"{url}\n\n")
            print(f"Created/Updated {file_name}")
    
    # Delete outdated m3u8 files
    for file in existing_files:
        if not any(file == f"{sha256sum(url)}.m3u8" for url in youtube_streams.values()):
            file_path = os.path.join(M3U8_DIR, file)
            os.remove(file_path)
            print(f"Deleted outdated file: {file}")

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

    generate_master_playlist(youtube_streams)
    update_m3u8_files(youtube_streams)
    git_commit_and_push()

if __name__ == "__main__":
    main()
