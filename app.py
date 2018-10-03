import tkinter as tk
from tkinter import ttk
import re
import fili2
import informator
import threading
import sys
import time
import queue

class ConfigChunk():
	MAX_DIGITS = 30
	def __init__(self, root, episode_list, url_list, series_name, id):
		self.episode_list = episode_list
		self.url_list = url_list
		self.id = id
		
		self.series_name = tk.Label(root, text=series_name)
		self.series_name.grid(row=self.id*3, column=0)
		
		self.start_slider = tk.Scale(root, to=len(self.episode_list)-1, command=self.start_check, orient="horizontal", showvalue=0, length=200)
		self.start_slider.grid(row=self.id*3+1, column=0)

		self.start_label = tk.Label(root, justify='left')
		self.start_label['text'] = self.episode_list[0]
		self.start_label.grid(row=self.id*3+2, column=0)

		self.end_slider = tk.Scale(root, to=len(self.episode_list)-1, command=self.end_check, orient="horizontal", showvalue=0, length=200)
		self.end_slider.set(len(self.episode_list))
		self.end_slider.grid(row=self.id*3+1, column=1)

		self.end_label = tk.Label(root, justify='left')
		self.end_label['text'] = self.episode_list[0]
		self.end_label.grid(row=self.id*3+2, column=1)
		
		self.start_check(self.start_slider.get()) #bo na początku może być za długa nazwa odcinka i sie rozjedzie
		self.end_check(self.end_slider.get())

	def start_check(self, value):
		new_value = self.episode_list[int(value)]
		if len(new_value) > self.MAX_DIGITS:
			new_value = new_value[0:self.MAX_DIGITS-3] + '...'
		self.start_label['text'] = new_value
		if self.end_slider.get() < int(value):
			self.end_slider.set(value)

	def end_check(self, value):
		new_value = self.episode_list[int(value)]
		if len(new_value) > self.MAX_DIGITS:
			new_value = new_value[0:self.MAX_DIGITS-3] + '...'
		#if len(new_value) < 20:
			
		self.end_label['text'] = new_value
		if self.start_slider.get() > int(value):
			self.start_slider.set(value)



class App():
	def __init__(self): 
		self.queue = queue.Queue()
		threading.Thread(target=self.create_app, daemon=True).start() #bcs calling fili2 in other thread than main will make problems, so run gui in other thread, daemon to have ability to exit
		time.sleep(0.5)
		while True:
			try:
				if self.root == None:
					break
				self.main_thread()
				time.sleep(0.1)
			except KeyboardInterrupt:
				print('KeyboardInterrupt')
				sys.exit(1)


	def main_thread(self):
		while True:
			try:
				callback = self.queue.get(False) 
			except queue.Empty: 
				break
			callback()
	
	
	def initialize(self):
		self.urls = self.get_urls(self.urls_box, self.urls_box.get('1.0', 'end-1c'))
		if not self.urls:
			informator.error('Sprawdź linki')
			return
			
		self.start_butt['command'] = self.start
		self.start_butt['text'] = 'Start'
	
		self.urls_box.destroy()
		self.config_box = tk.Frame(self.root)
		self.config_box.grid(column=0, row=0, sticky='NWSE')
		
		self.config_chunks = []
		for url in self.urls:	
			full_list = fili2.get_all_episodes(url)
			episode_list = ['['+fili2.get_ep_number(url)+'] '+episode for url, episode in full_list]
			url_list = [url for url, episode in full_list]
			series_name = fili2.get_name_of_series(full_list[0][0])
			#print(full_list)
			self.config_chunks.append(ConfigChunk(self.config_box, episode_list, url_list, series_name, self.urls.index(url)))
		
		
	def start(self):
		self.queue.put(self.start_download)
		
	def start_download(self):
		for i in range(len(self.urls)):
			start_index = self.config_chunks[i].start_slider.get()
			end_index = self.config_chunks[i].end_slider.get() + 1 
			url_list = self.config_chunks[i].url_list[start_index:end_index]
			episode_list = self.config_chunks[i].episode_list[start_index:end_index]
			
			full_list = []
			for i in range(len(url_list)):
				full_list.append((url_list[i], episode_list[i]))
			
			#print(self.audio_list.get()) #TO JEST Z MAŁYCH LITER I CHYBA NIE MOŻE BYĆ
			fili2.start_2(full_list, self.get_best_audio())
			#print(full_list)
		#if urls:
	#	fili2.start_2(urls)
		#else:
			#informator.error('Sprawdź linki')
			
	def get_best_audio(self):
		regex = {
					'Dubbing': 'DUBBING',
					'Lektor PL': 'LEKTOR_PL',
					'Napisy PL': 'NAPISY_PL', 
					'Angielski': 'ENG', 
					'Inne': 'INNE'
					}
		
		return regex[self.audio_list.get()]
	
	
	def is_valid_url(self, url): 
		regex = re.compile(
					r'^https://fili.cc/' 
					r'(?:serial|film)/'
					r'[\w-]+/' #the-100/
					r'[0-9]+$', re.IGNORECASE) #18
		return re.match(regex, url)

		
	def get_urls(self, urls_box, text):
		bad_url_tag = urls_box.tag_config("bad_url", foreground='red')
		default = urls_box.tag_config("normal", foreground='black')
		urls = text.split('\n')
		all_valid = True
		new_urls = []
		for url in urls:
			if url == '':
				continue
			if not self.is_valid_url(url):
				start_pos = urls_box.search(url, index=1.0) #start_pos ma typ string
				end_pos = str(int(float(start_pos))) + f'.{len(url)}' #najpierw zmieniam na int, żeby pozbyć się kropki, potem łącze linie z końcem
				urls_box.tag_add("bad_url", start_pos, end_pos)# f'{pos:.1f}', f'{pos+1.0:.1f}')
				all_valid = False
			else: #nadaje defaultowe, gdyby ktoś poprawił jedynie literówkę, bo inaczej zostanie reszta tekstu normalnie
				start_pos = urls_box.search(url, index=1.0) #start_pos ma typ string
				end_pos = str(int(float(start_pos))) + f'.{len(url)}' #najpierw zmieniam na int, żeby pozbyć się kropki, potem łącze linie z końcem
				urls_box.tag_delete("bad_url")
				new_urls.append(url)
		if all_valid == True:
			return new_urls
		return False
		

	def clear_placeholder(self, event):
		if self.urls_box.search('Podaj linki z fili.cc...', index=1.0, stopindex=2.0):
			self.urls_box.delete(1.0, 2.0)
	

	def create_app(self):
		#INITIALIZATION
		self.root = tk.Tk()
		self.root.title("Fili Downloader")
		#self.root.bind("<Destroy>", _delete_window)
		
		#URLS BOX
		self.urls_box = tk.Text(self.root, height=8, width=50, wrap='none')
		self.urls_box.tag_config("placeholder", foreground="#b2b2b2")
		self.urls_box.insert(1.0, 'Podaj linki z fili.cc... (np. https://fili.cc/serial/forever/7)', ('placeholder')) #miejsce insertion, placeholder, tag placeholdera
		self.urls_box.bind("<Button-1>", self.clear_placeholder) #usuwanie placeholdera gdy kliknie się na to
		self.urls_box.grid(row=0, column=0)

		#INFO BOX
		self.info_box = tk.Text(self.root, height=8, width=40, state='disabled', background='#cccccc', wrap='word')
		self.info_box.grid(row=0, column=1)

		#PROGRESS BAR
		self.dl_progress = ttk.Progressbar(self.root, orient='horizontal', length=730, mode='determinate') #length to powinien być width bo orient=horizontal, ale tak nie jest i nie wiem dlaczego, ale 570 idealnie pasuje
		self.dl_progress.grid(row=1, columnspan=2)
				
		#INFORMATOR
		informator.initialize(self.root, self.info_box, self.dl_progress)

		#dl_progress.start() #test

		#CHECKBUTTONS NA PÓŹNIEJ
		self.chckbt_frame = tk.Frame(self.root, width=50, bg='RED')
		self.chckbt_frame.grid(row=2, column=0, sticky='E')
		
		self.audio_list = ttk.Combobox(self.chckbt_frame, state='readonly')
		self.audio_list.grid(sticky='NSE')
		
		self.audio_list['values'] = ['Dubbing', 'Lektor PL','Napisy PL', 'Angielski', 'Inne']
		self.audio_list.set('Lektor PL')
		#for audio_name in ['Dubbing', 'Lektor PL','Napisy PL', 'Ang.', 'Inne']:
			#self.audio_list.insert('end', audio_name)
		# check_1 = tk.Checkbutton(chckbt_frame, text='TestAAAAAAA')
		# check_1.grid(row=0, column=0, sticky='W')

		# check_1 = tk.Checkbutton(chckbt_frame, text='Test2')
		# check_1.grid(row=0, column=1, sticky='W')

		# check_1 = tk.Checkbutton(chckbt_frame, text='Test3AAA')
		# check_1.grid(row=1, column=1, sticky='W')

		#PLACEHOLDER FOR CHECKBUTTONS
		#self.nothing = tk.Canvas(self.root, width=50, height=20)
		#self.nothing.grid(row=2, column=0)
		
		#START BUTTON
		self.start_butt = tk.Button(self.root, text='Initialize', command=self.initialize)#)lambda: start_download(lambda: start(self.urls_box))) #start
		self.start_butt.grid(row=2, column=1, sticky='WE')

		informator.info('Zainicjalizowano')

		self.root.mainloop() 

		self.root = None
	
	
App()
				
				
