import math

def saferatio(x,y):
	sx = max(1,float(x))
	sy = max(1,float(y))
	return sx/sy
#using a leading # will comment out a ranking
#allow rescaling of scoredifference for shorter than full-length bouts (no change needed for scoreratio)
rankfiles = [('rank1',60.0/40.0),('rank2345a',1.)]
data = []
names = set()
for r,scale in rankfiles:
	f = open(r,'r')
	for l in f:
		tmp = l.split()
		if tmp[0][0] == '#':
			print "Passing:"+tmp[0]
			continue
		names.add(tmp[0])
		names.add(tmp[2])
		winner = 1 if (int(tmp[1])>int(tmp[3])) else -1
		# Team 1, (win?), Team 2, (win?), scoredifference(scaled to full length) , log(scoreratio) (capped at blowouts), log(FTS normalised difference ratio)
		data.append( ( tmp[0].strip(), winner,tmp[2].strip(),0-winner,scale*abs(int(tmp[1])-int(tmp[3])), abs(math.log(saferatio(tmp[1],tmp[3]))), abs( (float(tmp[1])-float(tmp[3]))/(float(tmp[1])+float(tmp[3]))) ) )


print data

#alphabetically sort names for ranks
nameorder = sorted(names)
print nameorder 
n = open("names",'w')
for name in nameorder:
	n.write(name+"\n")
n.close()
#output our big matrix A and result vector y

A = open('Avector','w')
y = open('yvector','w')

#utility function to get the right elements in A (inefficient but data is more efficient in memory)
def n_win(l,n):
	if l[0]==n:
		return str(l[1])
	if l[2]==n:
		return str(l[3])
	return 0

for line in data:
	#y is a 2 column result vector for scorediff and scoreration, FTS normalised diff respectively
	y.write(str(line[4])+' '+str(line[5])+' '+str(line[6])+'\n')
	
	#A is a n-column team matrix for each line in the simultaneous equations
	Aline = ' '.join([ str(n_win(line,n)) for n in nameorder ])
	A.write(Aline+'\n')

A.close()
y.close()
