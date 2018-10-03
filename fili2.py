from urllib.request import Request, urlopen
from googleapiclient.discovery import build
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
api_key = 'AIzaSyABRWlxG0Ppm9fXusfqVjdRIrpFNZsHrqo'
cse_id = '005725991512029693991:tkqt7b-tjlo'
def search_link_from_google(name): #https://stackoverflow.com/questions/37083058/programmatically-searching-google-in-python-using-custom-search
	try:
		service = build("customsearch", 'v1', developerKey=api_key)
		res = service.cse().list(q=name, cx=cse_id, num=1).execute()
		#print(res)
		if 'items' in res:
			link = res['items'][0]['link']
			print('Link from google:', link)
			return link
	except:
		print(traceback.format_exc())
		print("Can't get link from google")
		return None
	
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
	
	#dodaje https://fili.cc do url, bo url = /serial/forever/s01e17/social-engineering/603
	new_full_episodes = [('https://fili.cc'+url, '['+get_ep_number(url)+'] '+name) for url, name in full_episodes] 
	
	return new_full_episodes

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
	name = re.search('/serial/([\w-]+)/s', episode_url).group(1).title().replace('-', ' ')
	return name

def get_name_of_movie(movie_url):
	m = re.search('/film/([\w-]+?)(\d\d\d\d)/', movie_url)
	name = m.group(1).title().replace('-', ' ')
	name = name[:-1] # usuwam ostatni znak, bo jest to ' ' (spacja). spowodowane to jest tym, 
									 # że zamieniam - na spacje a link wygląda tak: https://fili.cc/film/niebieska-malpa-1987/5737
	year = m.group(2)
	full_name = f'[{year}] {name}'
	return full_name

def get_name_of_episode(episode_url):
	name = re.search('/s\d\de\d\d/([\w-]+)/', episode_url).group(1).title().replace('-', ' ') #nazwa odcinka bez numeru
	full_name = '[' + get_ep_number(episode_url) + '] ' + name
	return full_name
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
			
def have_connection():
	try:
		with urlopen(url='https://google.pl'): # mam internet, więc zawinił jakiś z komponentów
			pass
		return True
	except:
		print('NIE MOGE SIĘ POŁĄCZYĆ (fili2)')
		return False
		
		
def start_2(full_list, dir_to_save, best_audio):
	series_name = get_name_of_series(full_list[0][0])
	for url, ep_name in full_list: #full_list = [('https://fili.cc/serial/the-art-of-more/s01e06/ride-along/40569', '[s01e06] Ride Along'), ('https://fili.cc/serial/the-art-of-more/s01e07/the-quatrefoil/40570', '[s01e07] The Quatrefoil')]
		path_name = f'{dir_to_save}/{series_name}/{ep_name}.mp4'
		if os.path.isdir(f"{dir_to_save}/{series_name}"):
			if os.path.exists(path_name):	
				informator.success(f'Już znajduje się na dysku: {series_name}/{ep_name}')
				continue
		else:
			os.mkdir(f"{dir_to_save}/{series_name}")
			
		get(path_name, url, best_audio)
		
		
def start_movie(full_url, dir_to_save, best_audio): 
	movie_name = get_name_of_movie(full_url)
	path_name = f'{dir_to_save}/Filmy/{movie_name}.mp4'
	if os.path.isdir(f'{dir_to_save}/Filmy'):
		if os.path.exists(path_name):
			print(f'Nie pobieram bo jest na dysku: {movie_name}')
			informator.inform(f'Już znajduje się na dysku: {movie_name}')
			return
	else:
		os.mkdir(f'{dir_to_save}/Filmy')
		
	get(path_name, full_url, best_audio)
	
	
def get(path_name, url, best_audio):
	def __get(path_name, url, best_audio): 
		f_links, audio_flinks = fili_links.get_fili_links(url, best_audio) #fili_links czyli linki embed, sel_audio_links czyli linki z wybranego audio
		host_links, audio_hlinks = down2.get_host_links(f_links, audio_flinks)
		download_links = down2.get_dl_links(host_links, audio_hlinks)
		down2.download(download_links, path_name)
	
	#def __get_from_dl_links
	while True:
		downloader.kill_printer()
		try:
			informator.info(f'Pobieram: {path_name}')
			__get(path_name, url, best_audio)
			informator.success(f"Pobrano: {path_name}!")
			break
		except: 
			if have_connection():
				print(traceback.format_exc())
				print(f"Can't get: {path_name}")
				informator.error(f"Nie udało się pobrać: {path_name}")
				break
			else: # nie mam internetu, więc czekam aż będę mieć i ponawiam
				while not have_connection(): 
					print('Trying to reconnect...')
					informator.warning('Próbuję się połączyć...')
					time.sleep(3)
		print('Connected!')
		informator.info('Połączono!')
		

#SŁUŻY DO POZYSKIWANIA LINKÓW JUŻ DO POBRANIA
def get_proper_links(url, best_audio):
	while True:
		try:
			f_links, audio_flinks = fili_links.get_fili_links(url, best_audio) #fili_links czyli linki embed, sel_audio_links czyli linki z wybranego audio
			host_links, audio_hlinks = down2.get_host_links(f_links, audio_flinks)
			download_links = down2.get_dl_links(host_links, audio_hlinks)
			return download_links
		except: 
			if have_connection():
				print(traceback.format_exc())
				print(f"Can't get proper links to: {url}")
				break
			else:
				while not have_connection(): 
					print('Trying to reconnect...')
					informator.warning('Próbuję się połączyć...')
					time.sleep(3)
				