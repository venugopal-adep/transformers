import streamlit as st
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from datetime import datetime
import re

# Page configuration
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #ff4b4b;
        margin-bottom: 1rem;
    }
    .subheader {
        font-size: 1.5rem;
        color: #666666;
        margin-bottom: 2rem;
    }
    .video-container {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #ddd;
    }
    .summary-section {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
        margin: 20px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .key-points {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .timestamp {
        color: #666666;
        font-size: 0.8rem;
    }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .error-message {
        color: #ff4b4b;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar for API key input
api_key = st.sidebar.text_input("Enter your OpenAI API Key", type="password")

# Initialize OpenAI client if API key is provided
client = None
if api_key:
    client = OpenAI(api_key=api_key)
else:
    st.sidebar.warning("Please enter your OpenAI API key to use this app.")

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_video_info(video_id):
    """Get video information using noembed API"""
    try:
        url = f"https://noembed.com/embed?url=https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url)
        data = response.json()
        return {
            'title': data.get('title', 'Unknown Title'),
            'author': data.get('author_name', 'Unknown Author'),
            'thumbnail': f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
        }
    except Exception as e:
        st.error(f"Error fetching video info: {str(e)}")
        return None

def get_transcript(video_id):
    """Get video transcript"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in transcript_list])
    except Exception as e:
        st.error("Could not fetch transcript. Please ensure the video has English subtitles.")
        return None

def generate_summary(transcript):
    """Generate comprehensive summary using GPT-3.5"""
    try:
        prompt = """
        Based on a YouTube transcript, write an eye-catching article for LinkedIn or Medium with a question-based title that hooks readers. 
        Incorporate specific data points, numbers, and structured details to ensure it’s authentic and engaging. 
        Add your own relevant insights to give the article depth, and use emojis for visual emphasis. 
        Organize each section to optimize readability and make the entire piece more likely to be shared, bookmarked, and commented on.
        Use story telling.
        Title and content should be sensational and viral
        """
        if client:
            response = client.chat.completions.create(
                model="gpt-4o-mini-2024-07-18",
                messages=[
                    {"role": "system", "content": "You are a professional content summarizer skilled in creating well-structured, comprehensive summaries with markdown formatting."},
                    {"role": "user", "content": f"{prompt}\n\nTranscript:\n{transcript[:4000]}"}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            return response.choices[0].message.content
        else:
            st.error("Please provide a valid OpenAI API key.")
            return None
    except Exception as e:
        st.error(f"Error generating summary: {str(e)}")
        return None

def main():
    # Header
    st.markdown("<h1 class='main-header'>🎥 YouTube Video Summarizer</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subheader'>Get comprehensive AI-powered summaries of YouTube videos</p>", unsafe_allow_html=True)

    # Input Section
    youtube_url = st.text_input("🔗 Enter YouTube Video URL", 
                               placeholder="https://www.youtube.com/watch?v=...")

    if youtube_url:
        video_id = extract_video_id(youtube_url)
        
        if not video_id:
            st.error("Invalid YouTube URL. Please check the URL and try again.")
            return

        with st.spinner("Processing video..."):
            # Get video information
            video_info = get_video_info(video_id)
            
            if video_info:
                # Display video information
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.image(video_info['thumbnail'], use_column_width=True)
                
                with col2:
                    st.markdown(f"""
                        <div class='video-container'>
                            <h2>{video_info['title']}</h2>
                            <p>Creator: {video_info['author']}</p>
                            <p class='timestamp'>Processed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        </div>
                    """, unsafe_allow_html=True)

                # Get and process transcript
                transcript = get_transcript(video_id)
                if transcript:
                    with st.spinner("Generating comprehensive summary..."):
                        summary = generate_summary(transcript)
                        
                        if summary:
                            # Display summary with markdown formatting
                            st.markdown("<div class='summary-section'>", unsafe_allow_html=True)
                            st.markdown(summary)
                            st.markdown("</div>", unsafe_allow_html=True)

                            # Additional features
                            with st.expander("📜 View Full Transcript"):
                                st.text(transcript)

                            # Download options
                            col1, col2 = st.columns(2)
                            with col1:
                                st.download_button(
                                    "📥 Download Summary",
                                    summary,
                                    file_name=f"summary_{video_id}.md",
                                    mime="text/markdown"
                                )
                            with col2:
                                st.download_button(
                                    "📥 Download Transcript",
                                    transcript,
                                    file_name=f"transcript_{video_id}.txt",
                                    mime="text/plain"
                                )

                            # Share button
                            st.markdown("---")
                            st.markdown("### Share this summary")
                            st.markdown(f"Video: [{video_info['title']}]({youtube_url})")

if __name__ == "__main__":
    main()
