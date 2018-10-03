from urllib.request import Request, urlopen, urlretrieve
from requests_html import HTMLSession
import urllib
import re
import sys
import time
import pickle
import traceback
import threading
import os
import requests
import downloader
import fili_links
import informator


useragent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0'
headers = {'User-Agent': useragent}

# def start(url, name, best_audio):
	# print("Starting: ", url, name)
	# informator.info(f"Zaczynam: {name}")
	# fili_links = get_fili_links(url, best_audio) #fili_links czyli linki embed
	# host_links, audio_hlinks = get_host_links(fili_links)
	# download_links = get_dl_links(host_links, audio_hlinks)
	# download(download_links, name)

# def start_2(fili_links, audio_flinks, name): #audio_flinks - fili links with selected audio
	# print("Starting: ", url, name)
	# informator.info(f"Zaczynam: {name}")
	# host_links = get_host_links(fili_links, audio_flinks)
	# download_links = get_dl_links(host_links, audio_hlinks)
	# download(download_links, name)
	
	
def get_host_links(fili_links, audio_flinks):
	host_links = []
	audio_hlinks = []
	for url in fili_links:
		req = Request(url, headers=headers)
		try:
			print("Avoiding captcha...")
			file_url = captcha_avoid(url)
			file_url = check_openload(file_url)
			host_links.append(file_url)
			if file_url in audio_flinks:
				audio_hlinks.append(file_url)
			print("Got it!")
		except:
			print(traceback.format_exc())
			print("Can't break captcha... Trying another link")
	set_no_proxy()
	return host_links, audio_hlinks
	
	
def check_openload(file_url):
	if file_url.startswith("https://openload.co"):
		return file_url.replace("embed", "f")
	return file_url
			
			
def captcha_avoid(url):
	import proxy_manager #tutaj to importuje, żeby nie było tego czekana na początku na GUI
	print(url)
	req = Request(url, headers=headers) 
	start_time = time.time()
	for proxy in proxy_manager.get_sorted_proxies():
		print(f"Trying with {proxy}")
		try:
			curr_headers = {'Connection': 'close',
				'User-Agent': useragent}
			proxies = {
				'https': 'http://' + str(proxy)}
			html = requests.get(url, headers=curr_headers, proxies=proxies, timeout=5).text
			file_url = re.search("var url = '(.+)';", html).group(1)
			print(file_url)
			print(f'Avoided! czas potrzebny: {time.time() - start_time}')
			#rank_proxy(proxy, 2)
			return file_url
		except:
			#print(traceback.format_exc())
			print("Oops! Give me a next try...")
			#rank_proxy(proxy, -7)
			continue
	raise Exception("Can't break captcha... :(")

def get_dl_links(host_links, audio_flinks):
	def __get(host_url):
		print(host_url)
		start_time = time.time()
		for i in range(3): #3 TRIES
			url = 'https://9xbuddy.app/process?url=' + urllib.parse.quote_plus(host_url)
			print(url)
			
			try:
				session = HTMLSession()
				buddy = session.get(url)
				print("Rendering...")
				buddy.html.render(keep_page=True)#to be sure about closing/EUREKA! with this i get links in 3 secs in one try
				print("Rendered")
				session.close()
				
			except:
				print(traceback.format_exc())
				session.close()
				continue
				
			try:
				dl_butt = buddy.html.xpath('//div[.="mp4"]/parent::div/following-sibling::div')[0]
				dl_link = dl_butt.links.pop() #te links to 'set' czyli coś jak przedział na matmie i trzeba zpopować to
				print(f"Got it in: {time.time()-start_time}")
				informator.info(f'Znaleziono link do pliku: {dl_link}')
				#dl_links.append(dl_link)
				return dl_link
				
			except Exception: #lxml.etree.XPathEvalError:
				#print(traceback.format_exc())
				print("Oops, failed :( Trying again...")
	
	
	def test_link(link):
		print('Testing link')
		informator.info('Sprawdzanie prędkości hosta')
		
		points = 0
		try:
			total_dl = 0
			with requests.get(link, timeout=5, stream=True) as r:
				t_end = time.time() + 8
				
				for chunk in r.iter_content(chunk_size=1024):
					if time.time() > t_end:
						break
					total_dl += len(chunk) #zamiast zapisywać tutaj sobie dodam i wyjdzie na to samo

				headers = r.headers #requests.head(link).headers

				if 'content-length' in headers:
					points += 10
					print('Content-length support!')
					
				if 'accept-ranges' in headers:
					print('Asynchronous downloading support!')
					points += 500
		except:
			print(traceback.format_exc())
			print(f"Can't connect to host... Avoiding this link: {link}")
			
		points += total_dl/30000
		print(f'{link} with performance: {points:.2f} points')
		rank[link] = points
		
	def check_audio(s):
		if s in audio_flinks:
			return 'a' # żeby umieścić na początku
		else:
			return 'z' # a tu na końcu 
	print("Searching for download links...")
	informator.info("Szukanie linków do plików...")
	dl_links = []
	rank = {}
	threads = []
	
	for link in host_links:
		dl_link = __get(link)
		if dl_link: #can't do threading, bcs html_requests doesn't work on other than main thread
			dl_links.append(dl_link)
			thread = threading.Thread(name='Speedtest', target=test_link, args=(dl_link,))
			threads.append(thread)
			thread.start()
		
	for thread in threads: 
		thread.join() #waiting for execute all tests
		
	if len(dl_links) == 0:
		raise Exception("Can't find any download link :/")
	else:
		sorted_links = []
		x = sorted(rank.items(), reverse=True, key=lambda i: i[1]) #items to: ((key1, value1), (key2, value2)...), sortuje punktami
		print('POINTS SORT:', [el[0] for el in x])
		x = sorted(x, key=lambda elem: check_audio(elem[0])) # sortuje tak, żeby najpierw były linki z audio posortowane punktami, a potem reszta
		for link, speed in x:
			sorted_links.append(link)
		
		print('FINAL SORT:', sorted_links)
		return sorted_links

		
def download(links, name):
	set_no_proxy()
	for link in links:
		try:
			print(f"Downloading from: {link}")
			informator.info("Pobieranie...")
			dl = downloader.start(link, name, 8)
			return #kończe pętle, bo pobrałem
		except Exception:
			print(traceback.format_exc())
			print("Something went wrong :( I'll try again...")
			informator.warning("Coś poszło nie tak... Próbuję jeszcze raz...")
			continue
	#jeśli doszło do tego momentu to żaden z linków nie zadziałał, najprawdopodobniej z powodu braku internetu
	raise Exception('Żaden z linków nie zadziałał (down2/download)')

def set_no_proxy():
	proxy = urllib.request.ProxyHandler(proxies=None)
	opener = urllib.request.build_opener(proxy)
	urllib.request.install_opener(opener)

