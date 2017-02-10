from math import cos, asin, sqrt
def distance(lat1, lon1, lat2, lon2):
    if lat2 is None:
	return 1000000
    p = 0.017453292519943295
    a = 0.5 - cos((lat2 - lat1) * p)/2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a))

#300 miles = 483km approx

teams = open("fts-teams_2016-10-01.augmented")

#manchester
#'lat:53.4807593,
#"lng" : -2.2426305

#Malmo
# "location" : {
#               "lat" : 55.604981,
#               "lng" : 13.003822
#            },

#Rotterdam
#"location" : {
#               "lat" : 51.9244201,
#               "lng" : 4.4777325
#            },

#Mons
#"location" : {
#               "lat" : 51.44296,
#               "lng" : 4.77062
#            },

source_coord=[51.443,4.771]

def safe_float(i):
	if i == 'None':
		return None
	return float(i)

max_dist=483.0
teams.readline()
redlines=[f.strip().split('|') for f in teams.readlines()]
lines= [i for i in redlines if max_dist > distance(source_coord[0],source_coord[1],safe_float(i[-2]),safe_float(i[-1]))]
lines2= [i for i in lines if i[4]=="Travel Team"]

print len(lines2)
print [l[2] for l in lines2]
