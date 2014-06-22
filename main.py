from urllib.request import urlretrieve
from urllib.request import urlopen
from mutagen.easyid3 import EasyID3
import mutagen
import sys
import re
import os
import copy


def main(reply):
	def f7(seq):
		seen = set()
		seen_add = seen.add
		return [x for x in seq if x not in seen and not seen_add(x)]

	def parse_username(user):
		url = "http://" + user + ".bandcamp.com"
		try:
			sock = urlretrieve(url)
		except:
			print("[!] That's not a valid username, perhaps try with a full url instead")
			sys.exit()
		ch = open(sock[0], encoding="ISO-8859-1").read()
		RE = re.compile('<span class="title">(.*?)</span>')
		new_user = ''
		try:
			new_user = RE.findall(ch)[0]
		except:
			print("[!] That's not a valid username")
			sys.exit()
		finally:
			if new_user:
				user = new_user
		RE = re.compile('/album/(.*?)">')
		albums = RE.findall(ch)
		for album in albums:
			print("Downloading Album: " + album)
			print("="*42)
			album_url = url + "/album/" + album
			sock = urlretrieve(album_url)
			ch = open(sock[0], encoding="ISO-8859-1").read()
			RE = re.compile('album_title : "(.*?)",')
			album_name = RE.findall(ch)
			RE = re.compile('artist : "(.*?)",')
			artist = RE.findall(ch)
			RE = re.compile("trackinfo : \[(.*?)\]", re.M)
			matches = RE.findall(ch)
			RE = re.compile('"title":"(.*?)","')
			titles = RE.findall(ch)
			titles = f7(titles)  # Remove stray duplicates, if any
			RE = re.compile('"file":{"mp3-128":"(.*?)"}')
			songs = RE.findall(ch)
			print(user)
			directory = os.path.join(user + "/" + album_name[0])
			print(directory)
			if not os.path.exists(directory):
				os.makedirs(directory)
			for i in range(len(songs)):
				title = titles[i].replace('"', '')
				track = str(i + 1)
				download(songs[i], title, album_name[0], artist[0], track, user)

	def simple_parse(url):
		# if not url[:7] == "http://":  # Failsafe, fails on https
		# 	url = "http://" + url
		try:
			sock = urlretrieve(url)
		except:
			print("[!] That's not a valid url")
			print("Example: http://derp.bandcamp.com")
			sys.exit()
		ch = open(sock[0], encoding="ISO-8859-1").read()
		RE = re.compile('album_title : "(.*?)",')
		new_user = ''
		try:
			new_user = RE.findall(ch)[0]
		except:
			print("[!] That's not a valid username")
			sys.exit()
		album_name = RE.findall(ch)
		RE = re.compile('artist : "(.*?)",')
		artist = RE.findall(ch)
		if not album_name:
			album_name = copy.deepcopy(artist)
		# RE = re.compile("trackinfo : \[(.*?)\]", re.M)
		# matches = RE.findall(ch)
		RE = re.compile('"title":"(.*?),"file"')
		titles = RE.findall(ch)
		titles = f7(titles)  # Remove any stray duplicates, if any
		RE = re.compile('"file":{"mp3-128":"(.*?)"}')
		songs = RE.findall(ch)

		directory = os.path.join(album_name[0])
		if not os.path.exists(directory):
			os.makedirs(directory)
		for i in range(len(songs)):
			title = titles[i].replace('"', '')
			track = str(i + 1)
			download(songs[i], title, album_name[0], artist[0], track)

	def download(download_url, title, album, artist, track, user=False):
		if user:
			file_name = "{}/{}/{}.mp3".format(user, album, title)
		else:
			file_name = "{}/{}.mp3".format(album, title)
		u = urlopen(download_url)
		try:
			f = open(file_name, 'wb')
		except:
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
		meta['tracknumber'] = track
		meta.save()

	print("Hold on, getting the relevant info...")
	if "bandcamp" in reply.split("."):
		simple_parse(reply)
	else:
		parse_username(reply)

if __name__ == '__main__':
	print("You have two options")
	print("Enter the full url to the album or track you wish to download")
	print("Or")
	print('Enter the username of the artist, and I will try to download everything the artist has made available, ("username".bandcamp.com)')
	reply = input("You must choose, but choose wisely: ")
	main(reply)