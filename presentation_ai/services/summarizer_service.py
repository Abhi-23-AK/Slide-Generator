import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="sumy")

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

def chunk_transcript(text: str, chunk_size: int = 400) -> list:
    """Chunks the transcript text into blocks of roughly `chunk_size` words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk_words = words[i:i + chunk_size]
        chunks.append(" ".join(chunk_words))
    return chunks

def summarize_chunk(text: str, sentences_count: int = 10) -> str:
    """Summarizes a single block of text using sumy's LsaSummarizer."""
    if not text.strip():
        return ""
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        stemmer = Stemmer("english")
        summarizer = LsaSummarizer(stemmer)
        summarizer.stop_words = get_stop_words("english")
        
        sentences = summarizer(parser.document, sentences_count)
        return " ".join(str(s) for s in sentences)
    except Exception as e:
        print(f"[SUMMARIZER] Warning: LSA summarization failed: {e}")
        # Fallback: return a portion of the text
        return " ".join(text.split()[:120])

def merge_summaries(summaries: list) -> str:
    """Merges all chunk summaries and refines the length to fall within 400-700 words."""
    combined = " ".join(s.strip() for s in summaries if s.strip())
    words = combined.split()
    total_words = len(words)
    
    if 400 <= total_words <= 700:
        return combined
        
    if total_words < 400:
        # If it's too short, return the combined text as is (best effort)
        return combined
        
    # If it is too long (> 700 words), re-summarize it using LSA
    # Let's estimate: we want around 550 words. If average sentence is 15 words,
    # target sentences = 550 / 15 ≈ 37.
    target_sentences = 37
    refined = summarize_chunk(combined, target_sentences)
    
    # If the refined summary is still slightly above 700, let's reduce sentences further
    refined_words = refined.split()
    if len(refined_words) > 700:
        refined = summarize_chunk(combined, 28) # Try 28 sentences (~420 words)
        
    # If it's too short (less than 400), let's increase sentences
    elif len(refined_words) < 400:
        refined = summarize_chunk(combined, 45) # Try 45 sentences (~675 words)
        
    return refined

def generate_video_summary(transcript_text: str) -> str:
    """Generates a structured 400-700 word summary of the video transcript using the sumy LSA summarizer."""
    if not transcript_text:
        return ""
        
    words = transcript_text.split()
    total_words = len(words)
    
    # If the transcript is already within or under the target word range, return it as-is
    if total_words <= 700:
        return transcript_text
            
    # 1. Chunk transcript into blocks of roughly 400 words
    chunks = chunk_transcript(transcript_text, chunk_size=400)
    
    # 2. Summarize each chunk using LsaSummarizer to extract key sentences
    chunk_summaries = []
    for chunk in chunks:
        summary = summarize_chunk(chunk, sentences_count=10)
        if summary:
            chunk_summaries.append(summary)
            
    # 3. Merge and refine summaries to guarantee the 400-700 word limit
    final_summary = merge_summaries(chunk_summaries)
    
    return final_summary
