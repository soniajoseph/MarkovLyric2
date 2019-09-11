from flask import render_template
from app import app
from MarkovModel import MarkovModel
from flask import request
import lyricsgenius, json

@app.route('/')
@app.route('/index')
def index():
	return render_template('index.html', title='Home')

@app.route('/about', methods=['POST', 'GET'])
def about():
	return render_template('about.html')

@app.route('/lyrics', methods=['POST'])
def lyrics():

	try: 
		# # Uncomment for RapGenius API
		# # get artist

		artist = request.form['artist']
		genius = lyricsgenius.Genius("Y_izF-J78Qf8qn1gqLTWyKj95b_sJuQwj7f4smPQq7zB1qnMp3mJ71jpB2tBu0Bb")


		genius.verbose = True # Turn off status messages
		genius.remove_section_headers = True # Remove section headers (e.g. [Chorus]) from lyrics when searching
		genius.skip_non_songs = True # Include hits thought to be non-songs (e.g. track lists)
		genius.excluded_terms = ["(Remix)", "(Live)"] # Exclude songs with these words in their title

		try:
			artist = genius.search_artist(artist, max_songs=8, sort="popularity")
		except:
			render_template('error.html', message="Artist not found.")


		# join lyrics into one document
		total_lyrics = []
		for song in artist.songs:
			total_lyrics.append(song.lyrics)
		total_lyrics = "".join(s for s in total_lyrics)

		model = MarkovModel()
		lyrics = model.textGenerator(total_lyrics, 10, 1000)
		lyrics = model.stringLyrics(lyrics)

		# add line breaks
		lyrics = lyrics.split('\n')

		return render_template('lyrics.html', lyrics=lyrics)

	except:
		return render_template('error.html', message="Enter a valid artist's name to start generating.")

