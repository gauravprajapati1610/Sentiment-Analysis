import os
from flask import Flask, render_template, send_from_directory
from flask import request
import io
import base64
from googleapiclient.discovery import build
import re
import emoji
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import seaborn as sns
import urllib.parse

app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')

# Route for sentiment analysis
@app.route('/analyze', methods=['post'])
def analyse_sentiment():
    API_KEY = 'Your key'  

    youtube = build('youtube', 'v3', developerKey=API_KEY) 


   
    video_id= request.form['Video_id'][-11:]
    

    #print("Video ID: " + video_id)

    # Getting the channelId of the video uploader
    video_response = youtube.videos().list(
        part='snippet',
        id=video_id
    ).execute()

    # Splitting the response for channelID
    video_snippet = video_response['items'][0]['snippet']
    uploader_channel_id = video_snippet['channelId']

    comments = []
    nextPageToken = None

    while len(comments) < 600:
        Request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,  
            pageToken=nextPageToken
        )
        response = Request.execute()
        for item in response['items']:
            comment = item['snippet']['topLevelComment']['snippet']
            # Check if the comment is not from the video uploader
            if comment['authorChannelId']['value'] != uploader_channel_id:
                comments.append(comment['textDisplay'])
        nextPageToken = response.get('nextPageToken')

        if not nextPageToken:
            break

   
    hyperlink_pattern = re.compile(
        r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')

    threshold_ratio = 0.65

    relevant_comments = []

  
    for comment_text in comments:
        comment_text = comment_text.lower().strip()

        emojis = emoji.emoji_count(comment_text)

        # Count text characters (excluding spaces)
        text_characters = len(re.sub(r'\s', '', comment_text))

        if (any(char.isalnum() for char in comment_text)) and not hyperlink_pattern.search(comment_text):
            if emojis == 0 or (text_characters / (text_characters + emojis)) > threshold_ratio:
                relevant_comments.append(comment_text)
    f = open("ytcomments.txt", 'w', encoding='utf-8')
    for idx, comment in enumerate(relevant_comments):
        f.write(str(comment) + "\n")
    f.close()

    def sentiment_scores(comment, polarity):
        
        sentiment_object = SentimentIntensityAnalyzer()

        sentiment_dict = sentiment_object.polarity_scores(comment)
        polarity.append(sentiment_dict['compound'])

        return polarity

    polarity = []
    positive_comments = []
    negative_comments = []
    neutral_comments = []

    f = open("ytcomments.txt", 'r', encoding='utf-8')
    comments = f.readlines()
    f.close()
    for index, items in enumerate(comments):
        polarity = sentiment_scores(items, polarity)

        if polarity[-1] > 0.05:
            positive_comments.append(items)
        elif polarity[-1] < -0.05:
            negative_comments.append(items)
        else:
            neutral_comments.append(items)

    avg_polarity = sum(polarity) / len(polarity)
    positive_count = len(positive_comments)
    negative_count = len(negative_comments)
    neutral_count = len(neutral_comments)
    labels = ['Positive', 'Negative', 'Neutral']
    comment_counts = [positive_count, negative_count, neutral_count]
# Creating bar chart
    plt.bar(labels, comment_counts, color=['green', 'red', 'grey'])
# Adding labels and title to the plot
    plt.xlabel('Sentiment')
    plt.ylabel('Comment Count')
    plt.title('Sentiment Analysis of Comments')

    img=io.BytesIO()
    plt.savefig(img,format='png')
    img.seek(0)
    plot_data= urllib.parse.quote(base64.b64encode(img.getvalue()).decode('utf-8'))
    return render_template('template.html',plot_url=plot_data)
if __name__ == '__main__':
    app.run(debug=True)

    
    
    
    
    
    
