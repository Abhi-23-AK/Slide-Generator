from youtube_transcript_api import YouTubeTranscriptApi

def fetch_transcript(video_id: str) -> str:
    """Fetches the full transcript text for a YouTube video using youtube-transcript-api with auto fallbacks."""
    try:
        # Retrieve the list of available transcripts (manual and auto-generated)
        transcript_list = YouTubeTranscriptApi().list(video_id)
        
        try:
            # Try to fetch English first
            transcript = transcript_list.find_transcript(['en'])
        except Exception:
            # Fall back to the first available transcript in any language
            transcript = next(iter(transcript_list))
            
        data = transcript.fetch()
        return " ".join(entry.text for entry in data)
    except Exception as e:
        raise ValueError(f"Failed to fetch YouTube transcript: {e}")
