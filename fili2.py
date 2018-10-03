from urllib.request import Request, urlopen
import informator
import urllib
import re
import sys
import fili_links
import down2
import downloader
import os
import traceback
import time

# def get_urls():
	# urls = []
	# for url in sys.argv:
		# urls.append(url)
	# return urls

def get_all_episodes(url):
	req = Request(url, headers={'User-Agent': 'Mozilla/5.0'}) #potrzebuje nagłówek, bo inaczej wykrywa mnie jako bota i odrzuca
	try:
		with urlopen(req) as response:
			html = response.read()
	except urllib.error.HTTPError:
		print("Can't connect to this site: " + url)
		raise Exception("wtf")
	html = html.decode('utf-8') #musze zdekodować bo html zapisany jest w bitach
	full_episodes = re.findall(r'<a class="episodeName" href="([\w/-]+)">(.+?)</a>', html) 

	return full_episodes

def get_seasons(url): #tutaj otrzymujemy zapis [sezon1[epizod1, epizod2...], sezon2[epizod1...]...]
	all_episodes, x = get_all_episodes(url)
	seasons = []
	curr_season = 0
	curr_episode = 0
	
	for episode in all_episodes:
		if curr_season != get_season_number(episode):
			curr_season += 1
			seasons.append([])
		seasons[curr_season-1].append(all_episodes[curr_episode])
		curr_episode += 1
	return seasons

def get_season_number(episode):
	season = re.search('s\d\de\d\d', episode).group()[1:3]
	return int(season)

def get_ep_number(episode): #episode to link
	curr_ep = re.search('s\d\de\d\d', episode).group()
	return curr_ep

def get_name_of_series(episode_url):
	name = re.search('/serial/([\w-]+)/s', episode_url).group(1).capitalize().replace('-', ' ')
	return name
	
#del sys.argv[0]
#urls = get_urls()
#url = sys.argv[0] #1 bo 0 to skrypt
# def start(urls): 
	# base_url = "https://fili.cc"
	# for url in urls: #całe seriale
		# print(url)
		# try:
			# full_episodes = get_all_episodes(url) #full_episode czyli url + name
			# series_name = get_name_of_series(full_episodes[0][0])
			# for ep, name in full_episodes:
				# try:
					# ep_name = f'{series_name}/[{get_ep_number(ep)}] {name}.mp4'
					# if os.path.isdir(series_name):
						# if os.path.exists(ep_name):
							# continue
					# else:
						# os.mkdir(series_name)
					# down2.start(base_url + ep, f'{ep_name}')
					# informator.success(f"Pobrano {ep_name}!")
				# except:
					# print(sys.exc_info()[0], sys.exc_info()[1], sys.exc_info()[2])
					# print(f"Can't get {get_ep_number(ep)}")
					# informator.error(f"Nie udało się pobrać {series_name}/[{get_ep_number(ep)}] {name}")
					# continue
			# informator.info(f"Pobrano odcinki z {series_name}")
		# except:
			# informator.error(f"Nie mogę pobrać {url}")
			# print(traceback.format_exc())

def start_2(full_list, best_audio):
	base_url = "https://fili.cc"
	series_name = get_name_of_series(full_list[0][0])
	print(series_name)
	for url, ep_name in full_list: #full_list = [('/serial/the-art-of-more/s01e06/ride-along/40569', '[s01e06] Ride Along'), ('/serial/the-art-of-more/s01e07/the-quatrefoil/40570', '[s01e07] The Quatrefoil')]
		try:
			print(f'Zaczynam: {ep_name}')
			informator.info(f'Zaczynam: {ep_name}')
			get(series_name, ep_name, base_url+url, best_audio)
			informator.success(f"Pobrano {ep_name}!")
		except:
			print(f"Can't download {ep_name}, trying again...")
			while True:
				#SHUTDOWN DOWNLOADING
				downloader.kill_all_chunks() 
				downloader.kill_printer()
				
				if have_connection():
					print(f"Can't get {get_ep_number(ep_name)}")
					informator.error(f"Nie udało się pobrać {series_name}/[{get_ep_number(ep_name)}]")
					print(traceback.format_exc())
					break
				else:
					while not have_connection(): #czekam aż będę miał połączenie
						print('Trying to reconnect...')
						informator.warning('Próbuję się połączyć...')
						time.sleep(3)
				print('Connected!')
				informator.info('Połączono!')
				try:
					informator.info(f'Próbuję ponownie: {ep_name}')
					get(series_name, ep_name, base_url+url, best_audio)
					informator.success(f"Pobrano {ep_name}!")
					break
				except: # nie mam internetu, więc czekam aż będę mieć i ponawiam
					print('Nie moge ponownie pobrac, lecz sprobuje jeszcze:', traceback.format_exc())
		
def get(series_name, ep_name, full_url, best_audio):
	ep_name = f'{series_name}/{ep_name}.mp4'
	if os.path.isdir(series_name):
		if os.path.exists(ep_name):
			return
	else:
		os.mkdir(series_name)
	f_links, audio_flinks = fili_links.get_fili_links(full_url, best_audio) #fili_links czyli linki embed, sel_audio_links czyli linki z wybranego audio
	host_links, audio_hlinks = down2.get_host_links(f_links, audio_flinks)
	download_links = down2.get_dl_links(host_links, audio_hlinks)
	down2.download(download_links, ep_name)
	
def have_connection():
	try:
		with urlopen(url='https://google.pl'): # mam internet, więc zawinił jakiś z komponentów
			pass
		return True
	except:
		print('NIE MOGE SIĘ POŁĄCZYĆ (fili2)')
		return False