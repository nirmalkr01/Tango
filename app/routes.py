from flask import render_template, request, redirect, url_for, flash
from app import app
from app.services.youtube_analyzer import analyze_youtube_video

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    youtube_link = request.form.get('youtube_link')
    if not youtube_link:
        flash('Please enter a valid YouTube link.', 'error')
        return redirect(url_for('home'))

    # Analyze the video
    analysis_result = analyze_youtube_video(youtube_link)

    if 'error' in analysis_result:
        flash(analysis_result['error'], 'error')
        return redirect(url_for('home'))

    return render_template('results.html', result=analysis_result)