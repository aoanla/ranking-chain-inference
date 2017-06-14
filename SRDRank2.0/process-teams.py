import csv,codecs,cStringIO
import sys
import urllib
import json
import time

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

ftsdata = []
with open(sys.argv[1],'rb') as ftsteamfile:
	ftsteamfile.readline() #remove the header
	reader = UnicodeReader(ftsteamfile)
	ftsdata = {r[0]:r[1:] for r in reader}

#ftsdata keyed by id

#denormalise
ks = ftsdata.keys()

for k in ks:
	v = ftsdata[k]
	if v[6] != u'':
		#lookup the owner team
		p_key = v[6]
		try:
			p_val = ftsdata[p_key]
		except:
			print "exception on key: " + p_key
			print "Parent team does not exist for key " + v[6]
		while p_val[6] != u'':
			p_key = p_val[6]
			try:
				tmp = p_val
				p_val = ftsdata[p_key]
			except:
				print "exception on key: " + p_key
				print "Parent team does not exist for key " + tmp
			#	print "Error, unable to recurse to Travel Team for:"
			#	print v
			#	sys.exit()
		ftsdata[k][1] = p_val[0] #use "team name" of travel team as our shortname field, as it better matches leaguename concept
		ftsdata[k][4] = p_val[4]
		ftsdata[k][9] = p_val[9]
		ftsdata[k][10] = p_val[10]

#load patches for location (id,location)
patches = []
with open("missing-teams-loc.psv",'rb') as f:
	patches = [i.decode("utf-8").strip().split(u"|") for i in f.readlines()]	

#only patch if we haven't already gotten a fix in our input file
for p in patches:
	if ftsdata[p[0]][4] == '':
		ftsdata[p[0]][4] = p[1] 

#add lat, lng, country
#quantise value to 0.02 units, approximately
def quantise(value):
	if value is None:
		return u'None'
	tmp = float(value)
	return unicode(int(tmp*50)/50.0)


def augment_loc(location):
	loc=''
	try:
		loc=urllib.quote_plus(location.encode('utf-8'),',')
	except:
		print location
		loc=''
	
	coords={}
	country = ""
	#lookup in our file cache of previous lookups
	filename='./Geoloc-cache/'+loc+'.out'
	try:
		response=open(filename)
		jsonrep=json.load(response)
		response.close()
		coords = jsonrep[u'results'][0][u'geometry'][u'location']
		#truncate coordinates to sensible values (quantise to 0.02 deg units, which is around 2km resolution)	
		addrs = jsonrep[u'results'][0][u'address_components']
		country = [ i[u'long_name'] for i in addrs if u'country' in i[u'types']][0]
		#in the final version, this try block is inside the try block which the exception handles
		#a fail to open above results in an exception to urlopen a query against the google API
		#and writing the result to the cache... which we then open
	except: 
		print "Failed:" + loc
		try: #cache miss
			errors.write("MISS:"+loc)
			if loc=='':
				errors.write(' NONE TYPE\n');
				coords = {u'lat':None,u'lng':None}
			else:
				urlstub = "https://maps.googleapis.com/maps/api/geocode/json?address="
				#key = "YOURGOOGLEAPIKEYHERE"
		       		urlloc = urlstub+loc+'&key='+key
	#			#wait here to avoid overloading Google API Free Geoloc ToS
				time.sleep(2)
	        		response = urllib.urlopen(urlloc)
				jsonrep=json.load(response)
				response.close()
				output = open(filename,'w')
				json.dump(jsonrep,output)
				output.close()
				coords = jsonrep[u'results'][0][u'geometry'][u'location']
				addrs = jsonrep[u'results'][0][u'address_components']
                		country = [ i[u'long_name'] for i in addrs if u'country' in i[u'types']][0]
				#errors.write("Would call: " + urlloc + '\n')
		except: #lookup fails in Google API - this except is a level deeper if we uncomment the above
			errors.write("Failed lookup:"+loc+'\n')
			coords = {u'lat':None,u'lng':None} 
	
	return [quantise(coords[u'lat']),quantise(coords[u'lng']),unicode(country)]

errors = open('errors','a')

for k in ks:
	loc_augment = augment_loc(ftsdata[k][4])
	ftsdata[k].extend(loc_augment)

dataout = open('teams-vector.uniform','w')
#keep country mappings const now for save compat - append if needed later
#countryout = open('country-vector.uniform','w')
teams = dict()

#country code mapping to series of bitfields
#for k,v in ftsdata.items():
#        if v[-1] in teams:
#                teams[v[-1]] += 1
#        elif v[-1] != '':
#                teams[v[-1]] = 1
#
#team_s = sorted(teams.keys(),key=lambda k: -teams[k])
#
tdict = {}
#var = 0
#sndvar = -1
#def safepow(v):
#	if v < 0:
#		return u'0'
#	else:
#		return unicode(1<<v)
#
#for k in team_s:
#	tmpvar = var
#	if var > 31:
#		sndvar +=1
#		tmpvar = -1
#	tdict[k]=[safepow(tmpvar),safepow(sndvar)]
#	countryout.write((u'|'.join([unicode(k),tdict[k][0],tdict[k][1]])+u'\n').encode('utf8'))
#	var += 1
#countryout.close()
tdict[u'']=[u'0',u'0']

countryin = open('country-vector.uniform','r')
l = countryin.readlines()
li = [i.split('|') for i in l]
tdict = {i[0]:[i[1],i[2]] for i in li}
countryin.close()
tdict[u'']=[u'0',u'0']

gender_dict={u'Womens':u'1',u'Mens':u'2',u'Coed':u'4',u'Junior':u'8',u'':u'0'}

for k,v in ftsdata.items():
        #  id, name, shortname, type, gender, lat, lng, country
        vector = [k,v[0],v[1],v[3],gender_dict[v[9]], v[-3],v[-2],tdict[v[-1]][0],tdict[v[-1]][1].strip()]
        #vuni = [unicode(v) for v in vector]
        dataout.write((u'|'.join(vector)+u'\n').encode('utf8'))
dataout.close()

