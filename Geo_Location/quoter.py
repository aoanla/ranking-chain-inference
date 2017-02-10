# -*- coding: utf-8 -*-
import urllib
import sys
import json
import time

errors = open('errors','a')
#output = open('output-a','a')

loc=''
try:
	loc=urllib.quote_plus(sys.argv[1],',')
except:
	loc=''

coords={}

#lookup in our file cache of previous lookups
filename='./Geoloc-cache/'+loc+'.out'
try:
	response=open(filename)
	jsonrep=json.load(response)
	response.close()
	coords = jsonrep[u'results'][0][u'geometry'][u'location']
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
			urlstub = "https://maps.googleapis.com/maps/api/geocode/json?address="
			key = "YOURGOOGLEAPIKEYHERE"
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
			#errors.write("Would call: " + urlloc + '\n')
	except: #lookup fails in Google API - this except is a level deeper if we uncomment the above
		errors.write("Failed lookup:"+loc+'\n')
		coords = {u'lat':None,u'lng':None} 
	

errors.close()
sys.stdout.write((unicode(coords[u'lat']) + u'|' + unicode(coords[u'lng'])+'\n').encode('utf8'))

