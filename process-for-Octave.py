import math
import time

datestart = time.mktime(time.strptime("01 Jan 13", "%d %b %y")) #start of sample training records
datelim = time.mktime(time.strptime("3 Nov 14", "%d %b %y"))   #end of sample training secords
datetest = datelim + 1 #3 months after datelim, end of testing records
#datelim = 1398898800.0

def saferatio(x,y):
	sx = max(1,float(x))
	sy = max(1,float(y))
	return sx/sy
#using a leading # will comment out a ranking
#allow rescaling of scoredifference for shorter than full-length bouts (no change needed for scoreratio)
rankfiles = [('FTS-stats.parsed',1.0),]
data = [[],[]]
names = set()
canonicalise = dict()
maxdate = datelim
#Get the list of short/long name mappings
f = open("short-long", 'r')
for l in f:
	tmp = l.split('@')
	shortname = tmp[0].strip()[1:-1].replace(" ", "_")
	longname = tmp[1].strip()[1:-1].replace(" ", "_")
	canonicalise[shortname] = longname
	canonicalise[longname] = longname
	names.add(longname)
f.close()

#parse the bouts
for r,scale in rankfiles:
	f = open(r,'r')
	for l in f:
		if l.strip() == '':
			continue
		tmp = l.split('@')
		if tmp[0][0] == '#':
			print "Passing:"+l
			continue
		date = time.mktime(time.strptime(tmp[0],"%m/%d/%y")) #seconds since epoch of bout happening
		#simple filter on age of records
		selector=0 #training
		if (date < datestart):
			continue
		elif (date > datelim):
			if (date > datetest):
				continue
			selector=1 #testing
			
		#if (date > maxdate):
		#	maxdate = date
		
		initialnames = (tmp[1].strip().replace(" ","_"), tmp[3].strip().replace(" ","_"))
		name = []
		for n in initialnames:
			try:
				name.append(canonicalise[n])
			except:
				name.append(n)
		names.add(name[0])
		names.add(name[1])
		winner = 1 if (int(tmp[2])>int(tmp[4])) else -1

		#home is the name of the hosting team, if there was one
		#for FTS data, this is the leftmost name in a bout, unless there's a tournament
		home = name[0] 
		# Team 1, (win?), Team 2, (win?), scoredifference(scaled to full length) , log(scoreratio) (capped at blowouts), log(FTS normalised difference ratio)
		data[selector].append( ( name[0], winner,name[1],0-winner,scale*abs(int(tmp[2])-int(tmp[4])), abs(math.log(saferatio(tmp[2],tmp[4]))), abs( (float(tmp[2])-float(tmp[4]))/(float(tmp[2])+float(tmp[4]))) , date, home) )


#print data

#alphabetically sort names for ranks
nameorder = sorted(names)
#print nameorder 
n = open("names",'w')
for name in nameorder:
	n.write(name+"\n")
n.close()
#output our big matrix A and result vector y

A = [open('Avector','w'),open('Avector_test','w')]
y = [open('yvector','w'),open('yvector_test','w')]
W = [open('Wvector','w'),open('Wvector_test','w')]
H = [open('Hvector','w'),open('Hvector_test','w')]

#utility function to get the right elements in A (inefficient but data is more efficient in memory)
def n_win(l,n):
	if l[0]==n:
		return str(l[1])
	if l[2]==n:
		return str(l[3])
	return 0

#returns the home advantage colum for the line in H (which is just the "home teams" column in A)
def h_adv(l,n):
	if l[8]==n:
		return n_win(l,n)
	return 0

for i in range(2):
	for line in data[i]:
		#y is a 2 column result vector for scorediff and scoreration, FTS normalised diff respectively
		y[i].write(str(line[4])+' '+str(line[5])+' '+str(line[6])+'\n')
		#W is the vector of dates (before the most recent record), for record optimisation
		W[i].write(str(datelim-line[7])+'\n')
		#A is a n-column team matrix for each line in the simultaneous equations
		Aline = ' '.join([ str(n_win(line,n)) for n in nameorder ])
		A[i].write(Aline+'\n')
		#H is a n-column team matrix for each line, giving the home team advantage marker
		Hline = ' '.join([ str(h_adv(line,n)) for n in nameorder ])
		H[i].write(Hline+'\n')
	H[i].close()
	W[i].close()
	A[i].close()
	y[i].close()
