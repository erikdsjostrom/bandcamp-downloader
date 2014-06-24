from urllib.request import urlretrieve
from urllib.request import urlopen
from mutagen.id3 import ID3, APIC, TIT2, TALB, TRCK, TPE1
import sys
import re
import os


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
            print("[!] That's not a valid username,\n\
perhaps try with a full url instead")
            sys.exit()
        ch = open(sock[0], encoding="ISO-8859-1").read()

        #Regex to find the artists/bands name, if it has one
        RE = re.compile('<span class="title">(.*?)</span>')
        new_user = None
        try:
            new_user = RE.findall(ch)
            for i in new_user:
                if i != '':
                    user = i
        except:
            """If it doesn't find a span with class="title",
               we know that it's not a valid username, because
               then it's not a valid bandcamp page"""
            print("[!] That's not a valid username")
            sys.exit()

        #Regex to find the different albums
        RE = re.compile('/album/(.*?)"')
        albums = RE.findall(ch)
        #Remove duplicates
        albums = f7(albums)
        for album in albums:
            print("Downloading Album: " + album)
            print("="*42)
            album_url = url + "/album/" + album

            #Read in the entire source of the pageon
            sock = urlretrieve(album_url)
            #Read the source
            ch = open(sock[0], encoding="ISO-8859-1").read()

            #Regex the title of the album
            RE = re.compile('album_title : "(.*?)",')
            album_name = RE.findall(ch)[0]

            #Regex the name of the artist
            RE = re.compile('artist : "(.*?)",')
            artist = RE.findall(ch)[0]

            #Regex to find the url to the album art
            RE = re.compile('<link rel="shortcut icon" href="(.*?)">')
            img_url = RE.findall(ch)[0]
            try:
                #Tries to download a temporary copy of the cover
                response = urlretrieve(img_url)[0]
                #Reads the data and saves it to img
                img = open(response, 'rb').read()
            except:
                #There might be cases where there is no cover art
                print("[!] No cover art found, sorry")
                img = False

            # Regex to find the parth of the page where
            # we find all the mp3's and titles
            RE = re.compile('trackinfo :(.*?)\}\],')
            # And saves this as it's own variable, this will keep
            # any stray duplicates out
            matches = RE.findall(ch)[0]

            #Regex to find all the different titles
            RE = re.compile('"title":"(.*?)","')
            titles = RE.findall(matches)

            # titles = f7(titles)  # Remove stray duplicates, if any

            #Regex all the different songs
            RE = re.compile('"file":{"mp3-128":"(.*?)"}')
            songs = RE.findall(matches)

            directory = os.path.join(user + "/" + artist + "-" + album_name)
            if not os.path.exists(directory):
                os.makedirs(directory)
            for i in range(len(songs)):
                title = titles[i].replace('"', '')
                track = str(i + 1)
                download(songs[i], title, album_name,
                         artist, track, img, user=user)

    def simple_parse(url):
        # if not url[:7] == "http://":  # Failsafe, fails on https
        #   url = "http://" + url

        try:
            sock = urlretrieve(url)
        except:
            print("[!] That's not a valid url")
            print("Example: http://derp.bandcamp.com")
            sys.exit()
        #Reads in the entire source of the page
        ch = open(sock[0], encoding="ISO-8859-1").read()
        #Regex for album name
        RE = re.compile('album_title : "(.*?)",')
        try:
            #Get's the name of the album
            album_name = RE.findall(ch)[0]
        except:
            #If it does not find an album name, there is no page
            print("[!] That's not a valid username")
            sys.exit()
        #Regex to find the url to the album art
        RE = re.compile('<link rel="shortcut icon" href="(.*?)">')  # Cover Art
        img_url = RE.findall(ch)[0]
        try:
            #Tries to download a temporary copy of the cover
            response = urlretrieve(img_url)[0]
            #Reads the data and saves it to img
            img = open(response, 'rb').read()
        except:
            #There might be cases where there is no cover art
            print("[!] No cover art found, sorry")
            img = False

        #Regex to find the name of the artist
        RE = re.compile('artist : "(.*?)",')
        artist = RE.findall(ch)[0]

        # Regex to find the parth of the page where
        # we find all the mp3's and titles
        RE = re.compile('trackinfo :(.*?)\}\],')
        # Saves this as it's own variable, this will keep
        # any stray duplicates out
        matches = RE.findall(ch)[0]

        #Regex all the titles that are stored in matches
        RE = re.compile('"title":"(.*?)",')
        titles = RE.findall(matches)

        #titles = f7(titles)  # Remove any stray duplicates, if any
        RE = re.compile('"file":{"mp3-128":"(.*?)"}')
        songs = RE.findall(matches)

        #Make a folder named "Artist name"-"Album name"
        directory = os.path.join(artist + "-" + album_name)
        if not os.path.exists(directory):
            os.makedirs(directory)
        for i in range(len(songs)):
            title = titles[i].replace('"', '').replace('\\', '')
            track = str(i + 1)
            download(songs[i], title, album_name, artist, track, img)

    def download(download_url, title, album, artist, track, img, user=False):
        if user:
            file_name = "{}/{}-{}/{}.mp3".format(user, artist, album, title)
        else:
            file_name = "{}-{}/{}.mp3".format(artist, album, title)
        u = urlopen(download_url)
        try:
            f = open(file_name, 'a+')
        except:
            print("Can't open file")
            pass
        finally:
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
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl *
                     100. / file_size)
            status = status + chr(8)*(len(status)+1)
            sys.stdout.write("\r" + status)
            sys.stdout.flush()

        f.close()
        tags = ID3()
        tags["TIT2"] = TIT2(encoding=3, text=title)
        tags["TALB"] = TALB(encoding=3, text=album)
        tags["TPE1"] = TPE1(encoding=3, text=artist)
        tags["TRCK"] = TRCK(encoding=3, text=track)
        tags["APIC"] = APIC(encoding=3, mime='image/jpeg', type=3, data=img)
        # I still haven't figured out a good way to find a suitable genre
        # tags["TCON"] = TCON(encoding=3, text=u'mutagen Genre')
        if img:  # If there is cover art
            tags["APIC"] = APIC(encoding=3, mime='image/jpeg',
                                type=3, data=img)
        tags.save(file_name)
    print("Hold on, getting the relevant info...")
    if "bandcamp" in reply.split("."):
        simple_parse(reply)
    else:
        parse_username(reply)

if __name__ == '__main__':
    os.system('clc' if os.name == "nt" else 'clear')  # Clear the terminal
    print("You have two options")
    print("Enter the full url to the album or track you wish to download")
    print("Or")
    print('Enter the username of the artist, and \n\
I will try to download everything the artist has made available')
    print("-"*42)
    print('A full url: http://"username".bandcamp.com')
    reply = input("[?] You must choose, but choose wisely: ")
    main(reply)
