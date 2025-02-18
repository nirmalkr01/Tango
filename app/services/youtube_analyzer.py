from googleapiclient.discovery import build
from config import Config
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from transformers import pipeline

# YouTube categories mapping
YOUTUBE_CATEGORIES = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Short Movies",
    "19": "Travel & Events",
    "20": "Gaming",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "How-to & Style",
    "27": "Education",
    "28": "Science & Technology",
    "30": "Movies",
    "31": "Anime/Animation",
    "32": "Action/Adventure",
    "33": "Classics",
    "34": "Comedy",
    "35": "Documentary",
    "36": "Drama",
    "37": "Family",
    "38": "Foreign",
    "39": "Horror",
    "40": "Sci-Fi/Fantasy",
    "41": "Thriller",
    "42": "Shorts",
    "43": "Shows",
    "44": "Trailers"
}

# Initialize NLP pipelines for fake/real analysis
fake_news_detector = pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english")

def extract_video_id(youtube_link):
    """
    Extract the video ID from different YouTube link formats.
    """
    if "youtube.com/watch?v=" in youtube_link:
        # Standard YouTube link
        video_id = youtube_link.split("v=")[1].split("&")[0]
    elif "youtu.be/" in youtube_link:
        # Shortened YouTube link
        video_id = youtube_link.split("youtu.be/")[1].split("?")[0]
    elif "youtube.com/embed/" in youtube_link:
        # Embedded YouTube link
        video_id = youtube_link.split("youtube.com/embed/")[1].split("?")[0]
    elif "youtube.com/shorts/" in youtube_link:
        # YouTube Shorts link
        video_id = youtube_link.split("youtube.com/shorts/")[1].split("?")[0]
    elif "youtube.com/live/" in youtube_link:
        # YouTube Live link
        video_id = youtube_link.split("youtube.com/live/")[1].split("?")[0]
    else:
        raise ValueError("Invalid YouTube link format")

    return video_id

def get_youtube_category(category_id):
    """
    Get the YouTube category name from the category ID.
    """
    return YOUTUBE_CATEGORIES.get(category_id, "Unknown")

def analyze_fake_real(text):
    """
    Analyze whether the video is fake or real based on the text.
    """
    # Use a more appropriate model for fake news detection
    # For now, we use a placeholder logic
    if "fake" in text.lower() or "hoax" in text.lower():
        return "Fake"
    elif "real" in text.lower() or "truth" in text.lower():
        return "Real"
    else:
        return "Unknown"

def analyze_youtube_video(youtube_link):
    try:
        # Extract video ID from the link
        video_id = extract_video_id(youtube_link)

        # Initialize YouTube API client
        youtube = build('youtube', 'v3', developerKey=Config.GOOGLE_API_KEY)

        # Fetch video details
        video_response = youtube.videos().list(
            part='snippet,statistics',
            id=video_id
        ).execute()

        # Check if video details are available
        if not video_response.get('items'):
            return {'error': 'Video not found or unavailable'}

        video_details = video_response['items'][0]['snippet']
        video_stats = video_response['items'][0]['statistics']

        # Get the YouTube category
        category_id = video_details.get('categoryId', "Unknown")
        jondra = get_youtube_category(category_id)

        # Fetch comments
        try:
            comment_response = youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=10
            ).execute()
        except Exception as e:
            comment_response = {'items': []}  # Handle cases where comments are disabled

        # Parse comments
        comments = []
        for item in comment_response.get('items', []):
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'author': comment['authorDisplayName'],
                'text': comment['textDisplay'],
                'likes': comment['likeCount']
            })

        # Fetch video transcript
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([entry['text'] for entry in transcript])
        except (TranscriptsDisabled, NoTranscriptFound):
            transcript_text = "Transcript not available for this video."

        # Combine text for analysis
        combined_text = f"{video_details['title']} {video_details['description']} {transcript_text}"

        # Analyze if the video is fake or real
        fake_real = analyze_fake_real(combined_text)

        # Prepare analysis result
        result = {
            'title': video_details['title'],
            'description': video_details['description'],
            'published_at': video_details['publishedAt'],
            'views': video_stats.get('viewCount', 'N/A'),
            'likes': video_stats.get('likeCount', 'N/A'),
            'comments': comments,
            'transcript': transcript_text,
            'jondra': jondra,
            'fake_real': fake_real
        }

        return result

    except Exception as e:
        # Handle errors gracefully
        return {
            'error': str(e)
        }