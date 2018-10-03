import os
import re
import informator
	
def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [atoi(c) for c in re.split('(\d+)', text)]

def start(filenames, ep_filename, buffer_parts):
	def merge(filenames, fout):
		for tmp_filename in filenames:
			print("Merging: " + tmp_filename)
			tmp_to_read = os.path.getsize(tmp_filename)
			buffer_size = tmp_to_read // buffer_parts
			buffer_point = 0
			try:
				while True:
					with open(tmp_filename, 'rb') as tmp:
						if buffer_size > tmp_to_read:
							buffer_size = tmp_to_read
					
						tmp.seek(buffer_point)
						readbytes = tmp.read(buffer_size)
						if readbytes:
							fout.write(readbytes)
							tmp_to_read -= buffer_size
							buffer_point += buffer_size
						else:
							print("Merging ended.")
							break
			except:
				print("Can't open tempfile...")
				raise Exception("Can't open: " + tmp_filename)
				break
			os.remove(tmp_filename)

	filenames = sorted(filenames, key=natural_keys)
	try:
		with open(ep_filename, 'wb') as fout:
			merge(filenames, fout)
	except OSError: #filename has char that can't be in filename
		ep_filename = ep_filename[:8]
		with open(ep_filename, 'wb') as fout:
			merge(filenames, fout)
		