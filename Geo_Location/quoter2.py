# -*- coding: utf-8 -*-
import urllib
import sys
import json
import time

errors = open('errors','a')
#output = open('output-a','a')

loc=''
try:
#	loc=urllib.quote_plus(sys.argv[1],',')
	loc="Oxford,+UK"
except:
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
	addrs = jsonrep[u'results'][0][u'address_components']
	country = [ i[u'long_name'] for i in addrs if u'country' in i[u'types']][0]
	#in the final version, this try block is inside the try block which the exception handles
	#a fail to open above results in an exception to urlopen a query against the google API
	#and writing the result to the cache... which we then open
except: 
	try: #cache miss
		errors.write("MISS:"+loc)
		if loc=='':
			errors.write(' NONE TYPE\n');
			coords = {u'lat':None,u'lng':None}
		else:
			#urlstub = "https://maps.googleapis.com/maps/api/geocode/json?address="
			#key = "YOURGOOGLEAPIKEYHERE"
	       		#urlloc = urlstub+loc+'&key='+key
#			#wait here to avoid overloading Google API Free Geoloc ToS
			#time.sleep(2)
        		#response = urllib.urlopen(urlloc)
			#jsonrep=json.load(response)
			#response.close()
			#output = open(filename,'w')
			#json.dump(jsonrep,output)
			#output.close()
			#coords = jsonrep[u'results'][0][u'geometry'][u'location']
			errors.write("Would call: " + urlloc + '\n')
	except: #lookup fails in Google API - this except is a level deeper if we uncomment the above
		errors.write("Failed lookup:"+loc+'\n')
		coords = {u'lat':None,u'lng':None} 
	

errors.close()
sys.stdout.write((unicode(coords[u'lat']) + u'|' + unicode(coords[u'lng'])+ u'|' + unicode(country) + '\n').encode('utf8'))

