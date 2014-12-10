import math
import collections
import random

NUM=10000
DEBUG=False
WARN=False
random.seed()

results = []
f = open('rank2')
for l in f:
	results.append(l.split('\t')[:4])
f.close()

def fuzz(score):
	#we have two kinds of fuzz
	# "jam scoring" fuzz - absolute gaussian fuzz representing variations in jams taken
	# "total score" fuzz - relative gaussian fuzz representing variations in performance over all scoring jams
	absfuzz = random.normalvariate(0,2) 
	relfuzz = random.normalvariate(1,0.02)
	return max(0, int(float(score)*relfuzz + absfuzz) )

def clampfloat(x):
	if x == '0' or x == 0:
		return 0.5
	return float(x)

def saferatio(x,y):
	return clampfloat(x)/clampfloat(y)

def fuzzratio(x,y):
	return saferatio(fuzz(x),fuzz(y))


#scoreweight is an arbitrary function designed to favour info from non-blowouts
def scoreweight(s):
#	return 1.0
	if s<1:
		s=1/s
	l = math.log(s)
	return math.sqrt(1/(1+l))


def prod(l):
	return reduce(lambda x,y: x*y,l,1.0)

#weighted reduce over inference chain provided, updating rankmatrix
def reduce_chains(name, rankmatrix, Chains, prime_rank, second_rank):
	#this is always true for our rank numbering
	dest_rank = prime_rank+second_rank+1
	if DEBUG:
		print "In reduce_chains"
		print str(prime_rank)+' '+str(second_rank)+' '+str(dest_rank)
	try:
		for chain in Chains[name]:
                	i = chain[0]
                	items = chain[1]
                	chainweight = sum([rankmatrix[name][j][prime_rank][1]*rankmatrix[j][i][second_rank][1] for j in items])
                	weightsum = sum([ prod(rankmatrix[name][j][prime_rank]) * prod(rankmatrix[j][i][second_rank]) for j in items])
                	finalweight = weightsum / chainweight
                	#invweightsum = sum([ 1/ (prod(rankmatrix[name][j][0]) * prod(rankmatrix[j][i][0]) ) for j in items])
                	#if the chained weight for the inverse relationship has not yet been calculated:
                	if rankmatrix[name][i][dest_rank][0] is None:
                       		rankmatrix[name][i][dest_rank] = [ finalweight  , chainweight]
                        	rankmatrix[i][name][dest_rank] = [ 1/finalweight , chainweight ]
                	#otherwise, we update in place, with the appropriate weighting
                	else:
                	        oldsum=rankmatrix[name][i][dest_rank][0]
                	        oldinvsum=rankmatrix[i][name][dest_rank][0]
                	        oldweight=rankmatrix[i][name][dest_rank][1]
                	        rankmatrix[name][i][dest_rank] = [ (oldsum*oldweight+weightsum)/(chainweight+oldweight), chainweight+oldweight ]
                	        rankmatrix[i][name][dest_rank] = [ (oldinvsum*oldweight+chainweight/finalweight)/(chainweight+oldweight), chainweight+oldweight ]
	except:
		if WARN:
			print "No chain for " + name + "at ranks " + str(prime_rank) + " " + str(second_rank)

#Generate n length inference chains from all existing shorter chains (previously generated)
#updates rankmatrix for all n-length chains in place
def gen_rank_n_chains(n, n_opps_flat, n_opps, Nples, Chains, rankmatrix, teams):
	n_opps_flat[n]=collections.defaultdict(set)
	for x,y in [(i,n-i-1) for i in range(0,n)]:
		Nples[x][y] = {}
		n_opps[x][y] = {}
		Chains[x][y] = {}
		if DEBUG:
			print "In gen rank chains"
			print str(x)+' '+str(y)+' '+str(n)
		for name in teams:
			n_opps[x][y][name] = [t for i in n_opps_flat[x][name] for t in n_opps_flat[y][i] if (t not in n_opps_flat[y][name])]
			Nples[x][y][name] = [(t,i) for i in n_opps_flat[x][name] for t in n_opps_flat[y][i] if (t not in n_opps_flat[y][name])]
			Chains[x][y][name] = [(i,[j[1] for j in Nples[x][y][name] if j[0]==i]) for i in set([i[0] for i in Nples[x][y][name]])]
			n_opps_flat[n][name] = n_opps_flat[n][name].union(set((n_opps[x][y][name])))
			reduce_chains(name, rankmatrix, Chains[x][y], x, y)

def trace_at_rankN(rankmatrix, N, teams):
	valid_values = [(i,rankmatrix[i][i][N-1][0]) for i in teams if rankmatrix[i][i][N-1][0] is not None]
	
	return sorted(valid_values, lambda x,y: cmp(x[1],y[1]))
		

def doranking(results):
	teams = list(set([i[2] for i in results]).union(set([i[0] for i in results])))
	ratios = [ (i[0],i[2],fuzzratio(i[1],i[3])) for i in results ] 
	#This is the full (900 element) pairwise rating matrix. The ratings for each pair are segmented in to first-hand (direct result of competition between pair), 2nd hand (result of competitions against competitors to the pair) and so on info
	rankmatrix = { i: {j:[[None,1],[None,1],[None,1],[None,1], [None,1]] for j in teams } for i in teams}

	#fill in diagonal
	for i in teams:
		rankmatrix[i][i][0][0] = 1.0

	#Fill in the first-hand ratings
	for item in ratios:
	        if item[2] == 0:
	                print "Zero Ranking violation"
	                print item
	                print "!!!!"
	        rankmatrix[item[0]][item[1]][0]=[item[2],scoreweight(item[2])]
	        rankmatrix[item[1]][item[0]][0]=[1/item[2],scoreweight(item[2])]

	n_opps_flat = collections.defaultdict(dict)
	n_opps_flat[0] = {}
	for name in teams:
	        n_opps_flat[0][name] = [i for i in rankmatrix[name] if rankmatrix[name][i][0][0] is not None]

	#make the initial datastructures
	n_opps = collections.defaultdict(collections.defaultdict)
	Nples = collections.defaultdict(collections.defaultdict)
	Chains = collections.defaultdict(collections.defaultdict)
	

	#Iteratively construct higher orders of inference chains until all pairings have at least one inferred ranking
	rank=0
	unranked = [ i for i in [ (k,l) for k in teams for l in teams if k != l] ] 
	#print "Total to rank:" + str(len(unranked))
	while (len(unranked) > 0):
		rank = rank+1
		gen_rank_n_chains(rank, n_opps_flat, n_opps, Nples, Chains, rankmatrix, teams)
		unranked = [ i for i in unranked if rankmatrix[i[0]][i[1]][rank-1][0] is None ]
		if WARN:
			print "At rank:" + str(rank) 
			print "self-ranks are:" + str(trace_at_rankN(rankmatrix, rank, teams))		
			print "Total self ranks:" + str(len(trace_at_rankN(rankmatrix, rank,teams)))
			print "Unranked " + str(len(unranked))

	convexity(teams, rankmatrix)

	#need to do the lambda to bind the local rankmatrix var
	#return sorted(teams, lambda x, y: ordering(x,y,rankmatrix))	
	return sorted(teams, anchored_ordering(rankmatrix, 'USA '))
	

identity = [(1,1)]*5
	
#emulate Maybe monad like reduction, stable if matrix is convex in rankings across inference chains
def maybe_reduce(x, y):  
	if x is None:
		return y[0]
	return x

def equal_rank_compare(x,y):
	pairs = [ i for i in zip(x,y) if x[0] is not None and y[0] is not None ]
	return cmp(i[0][0],i[1][0]) 



def anchored_ordering(rankmatrix, anchorname):
	 anchor_vector = rankmatrix[anchorname]
	 if DEBUG:
	 	print anchor_vector
	 #s = lambda p : identity if p==anchorname else anchor_vector[p]
	 s = lambda p : anchor_vector[p]
	 return lambda x,y: equal_rank_compare(s(x),s(y))

 

def ordering(name1, name2, rankmatrix):
	ordervec = rankmatrix[name1][name2]
	rank = reduce(maybe_reduce,ordervec, None)
	if rank is not None:	
		return cmp(1,rank)
	print "No comparison in table: " + name1 + " " + name2
	return 0 #no rating available



#Test convexity (shouldn't have any anomalies if the rankings are consistent across inference chains
def convexity(teams, rankmatrix):
	for i in teams:
		for j in teams:
			if i == j:
				continue
			vec = rankmatrix[i][j]
			vecsigns = [ k>1 for k in vec]
			for v in vecsigns[1:]:
				if (v!=vecsigns[0]):
					print "Anomalous ranking in " + i + " v " + j


teams = list(set([i[2] for i in results]).union(set([i[0] for i in results])))

histo= {}
lenteams = len(teams)
for n in teams:
	histo[n] = collections.defaultdict(lambda: 0)
for r in range(NUM):
	if (r%max(1,NUM/100) == 0): 
		print "Iteration: "+str(r)+"  ("+str((100*r)/NUM)+"%)"
	ranking = doranking(results)
	for j in range(lenteams):
		histo[ranking[j]][j] += 1
#	print ranking[29]
#	print histo[ranking[29]][29]

f = open('histo','w')
g = open('stats', 'w')
#h = open('num', 'w')
for n in teams:
	f.write(n + "," + ','.join([str(histo[n][i]) for i in range(lenteams)])+'\n') 
	mean = sum([histo[n][i]*i for i in range(lenteams)])/float(NUM)
	meansq = sum([histo[n][i]*i*i for i in range(lenteams)])/float(NUM)
	variance = meansq - mean*mean
	#the lenteams- adjusts for the backwards ranking
	g.write(n + "," + str(mean+1) + "," + str(variance) + '\n')

f.close()
g.close()

