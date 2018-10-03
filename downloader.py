import threading
import requests
import os
import merge
import time
import shutil
import gc
import informator 
	
total_downloaded = 0
dl_pause = False
dl_stop = False
#tmp_dir_path = 'tmp/'

DL_OK = True
class my_chunk(object):
	def __init__(self, url, start_byte, end_byte, id, tmp_dir_path):
		self.url = url
		self.start_byte = start_byte
		self.end_byte = end_byte
		self.curr_byte = start_byte
		self.id = str(id)
		self.filename = tmp_dir_path + self.id + '.tmp'
		self.headers = {}
		self.headers['Range'] = "bytes=" + str(self.start_byte) + "-" + str(self.end_byte)
		self.stop = False
		self.err_count = 0
		self.clear_tmp() #czyszcze plik temp który tu będzie użyty, bo ustawiłem tryb na ab przy zapisie więc inaczej będzie buuug
		self.thread = threading.Thread(name='DlChunk'+str(id), target=self.download, daemon=True)
		self.thread.start() #tu to robie, bo inaczej przy próbie dołączenia wywala Error nonetype
		self.supervisor = threading.Thread(target=self.supervisor, daemon=True).start()
	
	def clear_tmp(self):
		if os.path.exists(self.filename):
			os.remove(self.filename)

	def reconnect(self):
		print("Reconnecting...")
		self.stop = True
		self.thread.join() #dołączam, żeby czekać aż się wyłączy
		self.headers['Range'] = "bytes=" + str(self.curr_byte) + "-" + str(self.end_byte) #tworze nowy header
		self.stop = False
		self.thread = threading.Thread(target=self.download, daemon=True)
		self.thread.start()
	
	def reconnectv2(self):
		self.thread = threading.Thread(name="missing_files_downloader", target=self.download, daemon=True)
		self.headers['Range'] = "bytes=" + str(self.curr_byte) + "-" + str(self.end_byte) #tworze nowy header
		self.thread.start()
		self.thread.join()

	def download(self):
		print(f"STARTED: {self.curr_byte} SHOULD_START: {self.start_byte}")
		#r = requests.get(self.url, stream=True, headers=self.headers)
		try:
			with requests.get(self.url, stream=True, headers=self.headers, timeout=15) as self.r:
				with open(self.filename, 'ab') as f:
					for chunk in self.r.iter_content(chunk_size=1024):
						while dl_pause: # pauza stopuje
							time.sleep(1)
						#print("got")
						if self.stop == True: #do reconnecting
							print(f"Stopping at {self.curr_byte}")
							return
						if chunk:
							f.write(chunk)
							global total_downloaded
							total_downloaded += len(chunk)
						#	print(len(chunk))
							self.curr_byte += len(chunk)
						else:
							print("TMP downloaded")
							break
			print(F"ENDED: curr_byte: {self.curr_byte} end_byte: {self.end_byte}")
			if self.curr_byte-1 < self.end_byte: #nie wiem dlaczego, ale curr_byte zawsze kończy o 1 więcej niż end_byte (???)
				print("Downloading missing files...")
				self.reconnectv2()
		except:
			print("Trying again")
			self.err_count += 1
			if self.err_count <= 5:
				time.sleep(1)
				self.reconnectv2()
			else:
				global DL_OK
				DL_OK = False
				stop_downloading()
				raise Exception(f"Problems with host: 5 tries with bad results, host: {self.url}")
		print("TOTAL END " + self.filename)

	def supervisor(self): #nadzorowanie połączenia czy jest wystarczająco szybkie
		sizes = []
		while True:
			time.sleep(1)
			if self.stop == True:
				return
			if os.path.exists(self.filename):
				sizes.append(os.path.getsize(self.filename))
				if len(sizes) > 10:
					while len(sizes) > 10:
						sizes.pop(0)
					if sum(sizes) < 600000: #600 kB przez 10 sekund przez JEDNEGO chunka
						print("Download is slow, trying to get better result...")
						self.reconnect()
		
class printer(object):
	all_speeds = []
	def __init__(self, mode, filename=None, dl_size=None): #mode=async/sync'
		self.stop = False
		if mode == 'sync':
			threading.Thread(target=self.printer_sync, args=(filename,), daemon=True).start() #args-tworze tuple z jednym elementem (,)
		else:
			threading.Thread(target=self.printer_async, args=(dl_size,), daemon=True).start()
	
	def stop_printing(self):
		self.stop = True
	
	def printer_sync(self, filename):
		informator.init_bar()
		informator.bar_indtmt_start()
		downloaded = 0
		while True:
			if self.stop == True:
				break
			speed = (total_downloaded - downloaded)/1024
			downloaded = total_downloaded
			self.all_speeds.append(speed)
			if not os.path.exists(filename):
				print(f'{speed:.2f} KB/s ')
				time.sleep(1)
			else:
				avs = sum(self.all_speeds)/len(self.all_speeds)
				print(f"Avs: {avs:.2f}")
				break
		informator.stop_bar()
	
	def printer_async(self, dl_size):
		downloaded = 0
		dl_size = int(dl_size)
		informator.init_bar(determinate=True)
		while True:
			try:
				if self.stop == True:
					break
				speed = (total_downloaded - downloaded)/1024
				downloaded = total_downloaded
				percents = downloaded / dl_size * 100
				self.all_speeds.append(speed)
				if downloaded < dl_size-1:
					print(f'{speed:.2f} KB/s {percents:.2f}% SPRAWDZANIE: {downloaded, dl_size}')
					#informator.info(f'{speed:.2f} KB/s {percents:.2f}%')
					informator.bar_step(percents)
					time.sleep(1)
				else:
					avs = sum(self.all_speeds)/len(self.all_speeds)
					print(f"Avs: {avs:.2f}")
					break
			except TypeError: #int() argument must be a string, a bytes-like object or a number, not 'NoneType'
				break
		informator.stop_bar()

def stop_downloading():
	for obj in gc.get_objects():
		if isinstance(obj, my_chunk):
			obj.stop = True
	global dl_stop
	dl_stop = True

def kill_printer():
	for obj in gc.get_objects():
		if isinstance(obj, printer):
			obj.stop_printing()
			
def pause_downloading():
	global dl_pause
	dl_pause = True

def resume_downloading():
	global dl_pause
	dl_pause = False
	
def start(url, ep_name, chunk_count=8):
	global DL_OK
	DL_OK = True
	url = url
	ep_filename = ep_name
	headers = requests.head(url).headers
	size = 0
	#print(headers)
	if 'content-length' in headers:
		size = headers['content-length']

	if 'accept-ranges' in headers and size != 0:
		print("Asynchronous downloading")
		informator.info("Pobieram asynchronicznie")
		chunk_count = chunk_count
		chunk_dl_size = int(size)/chunk_count
		chunks = []
		
		tmp_dir_path = create_tmp_dir()

		for chunk_number in range(chunk_count):
			start_byte = int(chunk_number * chunk_dl_size)
			end_byte = int((chunk_number + 1) * chunk_dl_size - 1)
			new_chunk = my_chunk(url, start_byte, end_byte, chunk_number, tmp_dir_path)
			chunks.append(new_chunk)
			
		my_printer = printer(mode='async', dl_size=size)
		time.sleep(2) #żeby chunki się zainicjalizowały
		filenames = []
		for chunk in chunks:
			print(f'Aktywne rdzenie: {threading.active_count()}')
			chunk.thread.join()
			filenames.append(chunk.filename)
			
		active_chunks = len([thread for thread in threading.enumerate() if thread.name.startswith('DlChunk')])
		if active_chunks > 0: 
			print('Warning! Too many chunks')
			time.sleep(5)
		
		my_printer.stop_printing()
		stop_downloading()
		
		if DL_OK == True: #bo gdy nie pobierze się wszystko to po 5 próbach w każdym chunku to i tak się wykona, a plik wyjściowy będzie skoruptowany
			informator.info('Łączenie plików...')
			merge.start(filenames, ep_filename, chunk_count)
			clear(tmp_dir_path)
		else:
			informator.info('Coś poszło nie tak przy pobieraniu')
			clear(tmp_dir_path)
			raise Exception('Nie pobrałem dobrze pliku')
	else:
		with open(ep_filename + '.download', 'wb') as f:
			print("Normal downloading")
			informator.info("Pobieram normalnym sposobem")
			if size:
				my_printer = printer(mode='async', size=size)
			else:
				print("Downloading, but I can't give you much info about that process:")
				print(ep_filename)
				my_printer = printer(mode='sync', filename=ep_filename)
			sync_download(url, f, ep_name)
		if os.path.exists(ep_name + '.download'):
				os.rename(ep_name + '.download', ep_name)
				my_printer.stop_printing() #dla zgodności bo nie do końca może działać jeszcze
	set_default()
	

def sync_download(url, f, ep_name):
	try:
		r = requests.get(url, stream=True, timeout=40)
		for chunk in r.iter_content(chunk_size=1024): #1KB
			while dl_pause: # pauza stopuje
				time.sleep(1)
			if dl_stop: #służy temu, że jak wyłączysz program to przestanie pobierać
				return 
			if chunk:
				f.write(chunk)
				global total_downloaded
				total_downloaded += len(chunk)
			else:
				print("DOWNLOADED SYNCHRONOUS")
				#os.rename(ep_name + '.download', ep_name)
				break
	except Exception as e: #muszę to zrobić niestety, żeby przerwać printera gdy wystąpi jakiś błąd np timeout
		raise e

def create_tmp_dir():
	i = 0
	while True:
		tmp_name = 'tmp_' + str(i) + '/'
		try:
			os.mkdir(tmp_name)
			return tmp_name
		except FileExistsError:
			if try_to_clear(tmp_name): #jeśli true to oznacza, że ten folder był niepotrzebny i mogę go stworzyć od nowa
				#time.sleep(1)
				os.mkdir(tmp_name)
				return tmp_name
			i += 1

def try_to_clear(dir):
	files = os.listdir(dir)
	for file in files:
		try: #checking if file is in use 
			with open(dir+file, 'w+') as f:
				continue
		except:
			return False
	try: #sprawdzam dla bezpieczeństwa gdyby nagle coś zaczęło używać plik w złym momencie
		shutil.rmtree(dir, ignore_errors=True)
		while os.path.exists(dir): # check if it exists, bcs it can be not deleted and raise error on os.mkdir (os-dependent)
			pass
		return True
	except:
		return False
		
def set_default():
	global total_downloaded
	total_downloaded = 0

def clear(tmp_dir_path):
	print('Cleaning...')
	shutil.rmtree(tmp_dir_path)

# def test_p():
	# time.sleep(5)
	# pause_downloading()
	# time.sleep(5)
	# resume_downloading()

# threading.Thread(target=test_p).start()

# start('http://51.15.94.253/down/aHR0cHM6Ly9vcGVubG9hZC5jby9zdHJlYW0vNHdPRDJla3BRNWd-MTUzNzI4NTk1MH4yMDAxOmJjODo6fnh6N3l2RGNkP21pbWU9dHJ1ZQ,,/be79477c2bab104abb7cb6f191de334d-1537213954', 'test.mp4')
# print("ZAINICJALIZOWANO DOWNLOADERAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")


#start('https://www3826.playercdn.net/187/0/eE3ZhCY20UlCgLMzWuvCoA/1536434821/170625/471FGXM8NKKUTC4DBEQGX.mp4', "Otes2.mp4", 8)
#create_tmp_dir()

			