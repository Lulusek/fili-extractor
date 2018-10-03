import datetime

info_box = None
root = None
progress_bar = None
#INITIALIZING
def initialize(curr_root, curr_info_box, curr_progress_bar=None):
		global info_box
		info_box = curr_info_box
		info_box.tag_config('normal', foreground='black')
		info_box.tag_config('warning', foreground='#fffa00')
		info_box.tag_config('error', foreground='red')
		info_box.tag_config('success', foreground='green')
		global root
		root = curr_root
		if curr_progress_bar:
			global progress_bar
			progress_bar = curr_progress_bar

#NORMAL MESSAGE
def info(message):
	__add(message, 'info')

#WARNING
def warning(message):
	__add(message, 'warning')

#ERROR
def error(message):
	__add(message, 'error')

#SUCCESS
def success(message):
	__add(message, 'success')

#ADD
def __add(message, tag): #podlogi informuja o tym, ze to jest prywatna metoda
	if info_box:
		date_time = datetime.datetime.now()
		time = [str(date_time.hour), str(date_time.minute), str(date_time.second)]
		for i in range(len(time)): #type = currminute, currsecond...
			if len(time[i]) < 2:
				time[i] = '0' + time[i]
				
		stime = f'<{time[0]}:{time[1]}:{time[2]}> ' #string time
		end_message = stime + message + '\n'
		
		#ZMIENIANIE STATE ŻEBY MÓC NAPISAĆ COŚ
		info_box.config(state='normal')
		info_box.insert('end', end_message, tag)
		info_box.config(state='disabled')
		
		#USTAWIENIE WYŚWIETLANIA NA DÓŁ TEXTBOXA
		info_box.see('end')
		root.update()
	else:
		print('Initialize info_box first!')

def init_bar(determinate=False):
	if progress_bar:
		progress_bar.stop()
		progress_bar['value'] = 0
		if determinate:
			progress_bar['mode'] = 'determinate'
			progress_bar['maximum'] = 1000
		else:
			progress_bar['mode'] = 'indeterminate'
	else:
		print('Initialize progress bar first!')

def bar_step(percent_downloaded):
	if progress_bar:
		progress_bar['value'] = int(percent_downloaded*10) #*10 = zwiększam dokładność do 1/10 części
		root.update()

def bar_indtmt_start():
	if progress_bar:
		progress_bar.start(300)
		root.update()

def stop_bar():
	if progress_bar:
		progress_bar.stop()