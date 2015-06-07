import math


n = open("names",'r')
names = [ name.strip() for name in n ]
#print names
#print
n.close()


r = open("betavector",'r')
ranks = [ [float(i) for i in rank.split()] for rank in r if rank[0] != '#']
r.close()

combined = zip(names,ranks)

#print combined
#print



diffsort = [ (i[0],i[1][0]) for i in  sorted(combined, lambda x,y: cmp(y[1][0],x[1][0])) ] 
ratiosort = [ (i[0], i[1][1]) for i in  sorted(combined, lambda x,y: cmp(y[1][1],x[1][1]))  ]
#ftssort = [ (i[0], i[1][2]) for i in sorted(combined, lambda x,y: cmp(y[1][2],x[1][2])) ]

#PRINT OUT LISTS
offset = diffsort[0][1]
print "Rank with respect to Score Difference"
for i,n in zip(diffsort, range(1,len(diffsort)+1)):
	print str(n)+'. ' + i[0] + ' ' + str(i[1]-offset)

offset = ratiosort[0][1]
print "Rank with respect to Score Ratio"
for i,n in zip(ratiosort, range(1, len(diffsort)+1)):
	print str(n)+'. '+i[0] + ' ' + str( math.exp( i[1] - offset) )

#offset = ftssort[0][1]
#print "Rank with respect to FTS normalised Ratio"
#for i, n in zip(ftssort, range(1, len(ftssort)+1)):
#	print str(n)+'. '+i[0] + ' ' + str(math.exp( i[1] - offset) )
