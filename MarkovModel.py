import string, random, sys

class MarkovModel:

	# create Markov model of order k for specified text
	def markovModel(self, text, k):
		# make circular
		start = text[0:k]
		text = " ".join([text, start])
		kgrams = {}
		for i in range(0, len(text)-k, 1):
			key = text[i:i+k] # kgram
			char = text[i+k] # next character
			# put in kgram table
			if key not in kgrams:
				kgrams[key] = {}
			if char not in kgrams[key]:
				kgrams[key][char] = 1
			else:
				kgrams[key][char] += 1
		return kgrams

	# get next character in model by weighted probability
	def nextCharacter(self, kgrams, key):
		choice = []
		for letter in kgrams[key]:
			for count in range(0, kgrams[key][letter], 1):
				choice.append(letter)
		return random.choice(choice)

	# generate text character by character
	def textGenerator(self, text, k, characters):
		kgrams = self.markovModel(text, k)
		rand_idx = random.randint(0,len(text)-k-1)
		starting_kgram = text[rand_idx:rand_idx+k]
		lyrics = [starting_kgram]

		print(lyrics[0])
		for i in range(0, characters, 1):
			# print character
			char = self.nextCharacter(kgrams, starting_kgram)
			lyrics.append(char)
			print(char,end='')
			# update kgram
			starting_kgram = starting_kgram[1:] # remove first character
			starting_kgram = "".join([starting_kgram,char])# add new character

		return lyrics

	# generate string of lyrics
	def stringLyrics(self, lyrics):
		return "".join(lyrics)

if __name__ == "__main__":
	# f = open('bible.txt',"r")
	# text = f.read()

	# model = MarkovModel()

	# model.textGenerator(text, 6, 100)
	# print()
	# print()
	# print(model.stringLyrics())

	# textGenerator(text, int(sys.argv[2]), int(sys.argv[3]))

	print()