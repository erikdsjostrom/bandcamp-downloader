from urllib.request import urlretrieve
from urllib.request import urlopen
from mutagen.easyid3 import EasyID3
import mutagen
import sys
import re
import os

def main(url):
	def download(download_url, title, album, artist):
		file_name = "{}/{}.mp3".format(album, title)
		u = urlopen(download_url)
		f = open(file_name, 'wb')
		meta = u.info()
		file_size = int(meta["Content-Length"])
		print("Downloading: {} (Bytes: {})".format(title, file_size))

		file_size_dl = 0
		block_sz = 8192
		while True:
			buffer = u.read(block_sz)
			if not buffer:
				break

			file_size_dl += len(buffer)
			f.write(buffer)
			status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
			status = status + chr(8)*(len(status)+1)
			sys.stdout.write("\r" + status)
			sys.stdout.flush()

		f.close()
		try:
			meta = EasyID3(file_name)
		except mutagen.id3.ID3NoHeaderError:
			meta = mutagen.File(file_name, easy=True)
			meta.add_tags()
		meta['title'] = title
		meta['album'] = album
		meta['artist'] = artist
		meta.save()

	print("Hold on, getting the relevant info...")
	sock = urlretrieve(url)
	ch = open(sock[0]).read()
	RE = re.compile('album_title : "(.*?)",')
	album = RE.findall(ch)
	RE = re.compile('artist : "(.*?)",')
	artist = RE.findall(ch)
	RE = re.compile("trackinfo : \[(.*?)\]", re.M)
	matches = RE.findall(ch)
	try:
		RE = re.compile('"title":"(.*?),"file')
		titles = RE.findall(matches[0])
		RE = re.compile('"file":{"mp3-128":"(.*?)"}')
		songs = RE.findall(matches[0])
	except Exception as e:
		print("I can't download individual tracks right now, only albums. This might get fixed in the futured :)")
		print("You're welcome to try again, but this time with an actual album")
		sys.exit()

	directory = os.path.join(album[0])
	if not os.path.exists(directory):
		os.makedirs(directory)
	for i in range(len(songs)):
		title = titles[i].replace('"','')
		download(songs[i], title, album[0], artist[0])
	
	
if __name__ == '__main__':
	url = input("Enter the url of album you wish to download: ")
	main(url)