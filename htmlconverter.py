import re
import dragonmapper.hanzi

# test if unicode character is Chinese
def isChinese(char):
	return ord(char) >= 0x4E00 and ord(char) < 0x2B81F

# read cedict file
with open('cedict_ts.u8','r') as file:
	cedict = file.read()

# split into individual lines
lines = cedict.split("\n")

# initialize output lists
tradList = []
simpList = []
zhuyList = []
pinyList = []
meanList = []

# parsing
for l in lines:

	# ignore comments and empty lines
	if len(l)==0 or l[0]=="#":
		continue

	# escape apostrophe in json
	l = l.replace("'", "\\'")

	# traditional Chinese until first space
	traditional = l.split(" ")[0]

	# simplified Chinese between first and second space
	simplified = l.split(" ")[1]

	# zhuyin transcription chokes on some characters
	try:
		zhuyin = dragonmapper.hanzi.to_zhuyin(traditional)
	except:
		# transcribe characters individually if possible
		zhuyin = ""
		for i in range(len(traditional)):
			try:
				zhuyin += dragonmapper.hanzi.to_zhuyin(traditional[i])
			except:
				# character can't be transcribed, just use traditional
				zhuyin += traditional[i]

	# escape apostrophe for json
	zhuyin = zhuyin.replace("'", "\\'")

	# pinyin transcription and escape apostrophe for json
	pinyin = dragonmapper.hanzi.to_pinyin(traditional).replace("'", "\\'")

	# list of word meanings starts after first ]
	meanings = l[l.find("]")+3:-1]

	# remove all cedict pinyin
	meanings = re.sub("\[.*?\]", "", meanings)

	# iterate backwards through meaning strings and mark all Chinese symbols
	# (backwards so we don't have to mess with the iterators due to string length change)
	end=len(meanings)
	while end>=0:

		# we found the end of some Chinese
		if isChinese(meanings[end-1]):
			start=end-1

			# find start
			while isChinese(meanings[start-1]):
				start-=1

			# mark as traditional/pinyin/invariant using ascii control characters
			chin = meanings[start:end]
			if dragonmapper.hanzi.is_traditional(chin) and not dragonmapper.hanzi.is_simplified(chin):
				chin = chr(0x11) + chin + chr(0x14)
			elif dragonmapper.hanzi.is_simplified(chin) and not dragonmapper.hanzi.is_traditional(chin):
				chin = chr(0x12) + chin + chr(0x14)
			else:
				chin = chr(0x13) + chin + chr(0x14)

			meanings = meanings[:start] + chin + meanings[end:]

			end=start
		else:
			end-=1

	# remove split marks between traditional and simplified
	# meanings = meanings.replace("|", "")

	# turn into json list
	meanings = "['" + meanings.replace("/", "', '") + "']"

	# append to output lists
	tradList.append(traditional)
	simpList.append(simplified)
	zhuyList.append(zhuyin)
	pinyList.append(pinyin)
	meanList.append(meanings)

# convert all lists to json
js = ""
js += "traditional = ['" + "', '".join(tradList) + "']\n\n"
js += "simplified = ['" + "', '".join(simpList) + "']\n\n"
js += "zhuyin = ['" + "', '".join(zhuyList) + "']\n\n"
js += "pinyin = ['" + "', '".join(pinyList) + "']\n\n"
js += "meanings = [" + ", ".join(meanList) + "]\n\n"

# write to js file
with open('cedict.js','w') as file:
	file.write(js)

# read html template
with open('cedict_explorer_online.html','r') as file:
	html = file.read()

html = html.replace(
		"""<script src="cedict.js" charset="utf-8"></script>""",
		"<script>\n" + js + "\n</script>")

# write to html file
with open('cedict_explorer_offline.html','w') as file:
	file.write(html)
