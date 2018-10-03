from requests_html import HTMLSession
import time
import traceback
	
def get_fili_links(url, best_audio):
	try:
		if '/film/' in url:
			return get_movie(url, best_audio)
		else:
			return get(url, best_audio)
	except:
		print(traceback.format_exc())
		raise Exception(f'Cant get this: {url}')
		
		
def get(url, best='NAPISY_PL'):
	#print(best)
	session = HTMLSession()
	r = session.get(url)#('https://fili.cc/serial/riverdale/s01e07/rozdzial-siodmy-samotnosc/11931'
	if not r.ok: #CLOUDFLARE
		raise Exception('CloudFlare')
	data_codes_el = r.html.find('#episode_page')[0]
	code1, code2 = (data_codes_el.attrs['data-code'], data_codes_el.attrs['data-code2'])
	salts_containers = r.html.find('#links')[0]
	audio_types_el = salts_containers.find('[data-type]')
	
	all_salts = {		
		'DUBBING': [],
		'LEKTOR_PL': [],
		'NAPISY_PL': [],
		'ENG': [],
		'INNE': []
		} 

	for audio_type_el in audio_types_el:
		audio_type = audio_type_el.attrs['data-type']
		for salt_el in audio_type_el.find('li'):
			salt = salt_el.attrs['data-ref']
			host = salt_el.find('span.host')[0].text
			#print(host.text)
			if host != 'cda': # jak na razie brak obsługi cda
				try:
					all_salts[audio_type].append(salt)
				except KeyError:
					all_salts['INNE'].append(salt)
	audio_names = list(all_salts.keys())
	audio_names_sorted = get_audio_names_sorted(audio_names, best)	
	
	#print(audio_names_sorted)
	
	best_salts = []
	#audio_names = all_salts.keys() #['LEKTOR_PL', 'NAPISY_PL', 'ENG', 'INNE'] 
	for audio_name in audio_names_sorted:
		while len(best_salts) < 5:
			try:
				best_salts.append(all_salts[audio_name][len(best_salts)])
			except IndexError:
				break
				
	fili_links = []	
	for salt in best_salts:
		fili_links.append(f'https://fili.cc/embed?type=episode&code={code1}&code2={code2}&salt={salt}')
	
	audio_type_links = []
	for salt in all_salts[best][0:5]: #tylko linki z wybranego audio type
		audio_type_links.append(f'https://fili.cc/embed?type=episode&code={code1}&code2={code2}&salt={salt}')
		
	return fili_links, audio_type_links

def get_audio_names_sorted(audio_names, best):
	try:
		best_audio_index = audio_names.index(best)
	except ValueError: #best_audio is not in the list
		best_audio_index = audio_names.index('LEKTOR_PL')
	
	audio_names_sorted = []
	count = best_audio_index
	a = best_audio_index
	for i in range(len(audio_names)):
		audio_names_sorted.append(audio_names[best_audio_index])
		if count == 0:
			best_audio_index = a+1
		elif count < 0:
			best_audio_index += 1
		else:
			best_audio_index -= 1
		count -= 1
		
	return audio_names_sorted


def get_movie(url, best='NAPISY_PL'):
	session = HTMLSession()
	r = session.get(url)#('https://fili.cc/serial/riverdale/s01e07/rozdzial-siodmy-samotnosc/11931'
	if not r.ok: #CLOUDFLARE
		#time.sleep(6)
		raise Exception('CloudFlare')
	data_codes_el = r.html.find('#movie_page')[0]
	code1 = (data_codes_el.attrs['data-code'])
	code2 = 'undefined'
	salts_containers = r.html.find('#links')[0]
	audio_types_el = salts_containers.find('[data-type]')
	
#	host = sa
	
	
	all_salts = {		
		'DUBBING': [],
		'LEKTOR_PL': [],
		'NAPISY_PL': [],
		'ENG': [],
		'INNE': []
		} 

	for audio_type_el in audio_types_el:
		audio_type = audio_type_el.attrs['data-type']
		for salt_el in audio_type_el.find('li'):
			salt = salt_el.attrs['data-ref']
			host = salt_el.find('span.host')[0].text
			if host != 'cda':
				try:
					all_salts[audio_type].append(salt)
				except KeyError:
					all_salts['INNE'].append(salt)

	audio_names = list(all_salts.keys())
	audio_names_sorted = get_audio_names_sorted(audio_names, best)	
	
	#print(audio_names_sorted)
	
	best_salts = []
	#audio_names = all_salts.keys() #['LEKTOR_PL', 'NAPISY_PL', 'ENG', 'INNE'] 
	for audio_name in audio_names_sorted:
		while len(best_salts) < 5:
			try:
				best_salts.append(all_salts[audio_name][len(best_salts)])
			except IndexError:
				break
	
	fili_links = []	
	for salt in best_salts:
		fili_links.append(f'https://fili.cc/embed?type=movie&code={code1}&code2={code2}&salt={salt}')
	
	audio_type_links = []
	for salt in all_salts[best][0:5]: #tylko linki z wybranego audio type
		audio_type_links.append(f'https://fili.cc/embed?type=movie&code={code1}&code2={code2}&salt={salt}')
		
	return fili_links, audio_type_links
#print(get('https://fili.cc/serial/rozczarowani/s01e05/faster-princess-kill-kill/43596'))
#lektor = r.html.find('ul~[data-type="LEKTOR_PL"]')[0]
#print(lektor)
#print(lektor.absolute_links)