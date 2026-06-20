import re
import requests

def extract_video_id(url: str) -> str:
    """Extracts the 11-character YouTube video ID from a URL."""
    if not url:
        raise ValueError("YouTube URL is empty.")
    
    # Regex patterns for various YouTube URL formats
    patterns = [
        r'(?:v=|\/v\/|embed\/|shorts\/|youtu\.be\/|\/watch\?v=|\&v=)([^#\&\?]+)',
        r'youtu\.be\/([^#\&\?]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            vid = match.group(1)
            if len(vid) == 11:
                return vid
                
    # If it's already an 11-char ID
    stripped = url.strip()
    if len(stripped) == 11:
        return stripped
        
    raise ValueError("Could not extract a valid 11-character YouTube Video ID.")

def parse_iso8601_duration(duration_str: str) -> float:
    """Parses ISO 8601 duration string (e.g. PT8M4S) into seconds."""
    pattern = re.compile(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?')
    match = pattern.match(duration_str)
    if not match:
        return 0.0
    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0
    return float(hours * 3600 + minutes * 60 + seconds)

def get_video_duration(video_id: str) -> float:
    """Fetches video duration in seconds from the YouTube watch page without API keys."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code == 200:
            html = resp.text
            
            # Method 1: parse <meta itemprop="duration" content="PT8M4S">
            meta_match = re.search(r'<meta itemprop="duration" content="([^"]+)"', html)
            if meta_match:
                val = meta_match.group(1)
                dur = parse_iso8601_duration(val)
                if dur > 0:
                    return dur
                    
            # Method 2: parse approxDurationMs
            ms_match = re.search(r'"approxDurationMs"\s*:\s*"(\d+)"', html)
            if ms_match:
                return float(ms_match.group(1)) / 1000.0
    except Exception:
        pass
        
    # Fallback to transcript duration
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        transcript_list = YouTubeTranscriptApi().list(video_id)
        transcript = next(iter(transcript_list))
        data = transcript.fetch()
        if data:
            last_entry = data[-1]
            return float(last_entry.start + last_entry.duration)
    except Exception as e:
        raise ValueError(f"Failed to retrieve YouTube video duration (both watch page and transcript fallback failed): {e}")
        
    raise ValueError("Could not extract video duration metadata from watch page or transcript.")

def validate_duration(duration: float):
    """Checks if the video is within the maximum supported duration of 10 minutes (600 seconds)."""
    # Returns (is_valid, msg)
    if duration > 600.0:
        return False, "Only videos up to 10 minutes are supported."
    return True, ""
