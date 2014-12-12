import math
import collections
import random
from functools import reduce

NUM=10000
DEBUG=False
WARN=False
INFO=False
FUZZ=True
random.seed()

results = []
f = open('rank2')
for l in f:
	results.append(l.split('\t')[:4])
f.close()


#Topological sort (from http://code.activestate.com/recipes/577413-topological-sort/ )
#http://code.activestate.com/recipes/578272-topological-sort/
def toposort2(data):
    """Dependencies are expressed as a dictionary whose keys are items
and whose values are a set of dependent items. Output is a list of
sets in topological order. The first set consists of items with no
dependences, each subsequent set consists of items that depend upon
items in the preceeding sets.

>>> print '\\n'.join(repr(sorted(x)) for x in toposort2({
...     2: set([11]),
...     9: set([11,8]),
...     10: set([11,3]),
...     11: set([7,5]),
...     8: set([7,3]),
...     }) )
[3, 5, 7]
[8, 11]
[2, 9, 10]

"""


    # Ignore self dependencies.
    for k, v in data.items():
        v.discard(k)
    # Find all items that don't depend on anything.
    extra_items_in_deps = reduce(set.union, data.itervalues()) - set(data.iterkeys())
    # Add empty dependences where needed
    data.update({item:set() for item in extra_items_in_deps})
    while True:
        ordered = set(item for item, dep in data.iteritems() if not dep)
        if not ordered:
            break
        yield ordered
        data = {item: (dep - ordered)
                for item, dep in data.iteritems()
                    if item not in ordered}
    #original code throws an assertion on cycles
    #we just return the set of cycle as an equivalence class for the next iteration to break
    assert not data, "Cyclic dependencies exist among these items:\n%s" % '\n'.join(repr(x) for x in data.iteritems())
    #yield set([x for x in data.iteritems()])

def max_find_none(vector,maxrank):
	v = None
	for i in range(0,min(len(vector),maxrank)):
		if vector[i][0] is not None:
			v = vector[i][0]
			break
	return v
   

def build_dep_dict(teams, rankmatrix, dep_dict, maxrank = 10000):
	for i in teams:
		dep_dict[i] = set() 
		for j in teams:
			valvec = rankmatrix[i][j]
			v = max_find_none(valvec,maxrank)
			if v > 0:
				dep_dict[i].add(j)

	
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

def logratio(x,y):
	return math.log(fuzzratio(x,y)) if (FUZZ) else math.log(saferatio(x,y))

def saferatio(x,y):
	return clampfloat(x)/clampfloat(y)

def fuzzratio(x,y):
	return saferatio(fuzz(x),fuzz(y))


#scoreweight is an arbitrary function designed to favour info from non-blowouts
def scoreweight(s):
#	return 1.0
	s = abs(s)
	return math.sqrt(1/(1+s))


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
                	weightsum = sum([ rankmatrix[name][j][prime_rank][1]*rankmatrix[j][i][second_rank][1]*(rankmatrix[name][j][prime_rank][0]+rankmatrix[j][i][second_rank][0]) for j in items])
                	finalweight = weightsum / chainweight
                	#invweightsum = sum([ 1/ (prod(rankmatrix[name][j][0]) * prod(rankmatrix[j][i][0]) ) for j in items])
                	#if the chained weight for the inverse relationship has not yet been calculated:
                	if rankmatrix[name][i][dest_rank][0] is None:
                       		rankmatrix[name][i][dest_rank] = [ finalweight  , chainweight]
                        	rankmatrix[i][name][dest_rank] = [ 0-finalweight , chainweight ]
                	#otherwise, we update in place, with the appropriate weighting
                	else:
                	        oldsum=rankmatrix[name][i][dest_rank][0]
                	        oldinvsum=rankmatrix[i][name][dest_rank][0]
                	        oldweight=rankmatrix[i][name][dest_rank][1]
                	        rankmatrix[name][i][dest_rank] = [ (oldsum*oldweight+weightsum)/(chainweight+oldweight), chainweight+oldweight ]
                	        rankmatrix[i][name][dest_rank] = [ (oldinvsum*oldweight-weightsum)/(chainweight+oldweight), chainweight+oldweight ]
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
	valid_values = [(i,rankmatrix[i][i][N-1]) for i in teams if rankmatrix[i][i][N-1][0] is not None]
	
	return sorted(valid_values, lambda x,y: cmp(x[1],y[1]))
		

def doranking(results):
	teams = list(set([i[2] for i in results]).union(set([i[0] for i in results])))
	ratios = [ (i[0],i[2],logratio(i[1],i[3])) for i in results ] 
	#This is the full (900 element) pairwise rating matrix. The ratings for each pair are segmented in to first-hand (direct result of competition between pair), 2nd hand (result of competitions against competitors to the pair) and so on info
	rankmatrix = { i: {j:[[None,1],[None,1],[None,1],[None,1], [None,1]] for j in teams } for i in teams}

	#fill in diagonal
	for i in teams:
		rankmatrix[i][i][0][0] = 0.0

	#Fill in the first-hand ratings
	for item in ratios:
	        #if item[2] == 0:
	        #        print "Zero Ranking violation"
	        #        print item
	        #        print "!!!!"
	        rankmatrix[item[0]][item[1]][0]=[item[2],scoreweight(item[2])]
	        rankmatrix[item[1]][item[0]][0]=[0-item[2],scoreweight(item[2])]

	n_opps_flat = collections.defaultdict(dict)
	n_opps_flat[0] = {}
	for name in teams:
	        n_opps_flat[0][name] = [i for i in rankmatrix[name] if rankmatrix[name][i][0][0] is not None]

	#make the initial datastructures
	n_opps = collections.defaultdict(collections.defaultdict)
	Nples = collections.defaultdict(collections.defaultdict)
	Chains = collections.defaultdict(collections.defaultdict)
	if INFO:
		print "*******RANK 0********"
	dep_dict = {}
	topo_classes_by_rank = []
        build_dep_dict(teams, rankmatrix, dep_dict, maxrank = 10000)
	try:
		topo_classes_by_rank.append([x for x in toposort2(dep_dict)])
	except:
		topo_classes_by_rank.append([set(teams)])
        if INFO:
		print '\n'.join(','.join(e for e in x) for x in topo_classes_by_rank[0])
		print "**********************"
	
	#Iteratively construct higher orders of inference chains until all pairings have at least one inferred ranking
	rank=0
	needs_sorting=True #always true at the start
	unranked = [ i for i in [ (k,l) for k in teams for l in teams if k != l] ] 
	#print "Total to rank:" + str(len(unranked))
	#We need to continue sorting until either all teams have a unique rank (needs_sorting is False)
	# 				or there are no more pairs of info to construct (len(unranked)==0)
	while (needs_sorting and len(unranked)!=0):
		rank = rank+1
		gen_rank_n_chains(rank, n_opps_flat, n_opps, Nples, Chains, rankmatrix, teams)
		unranked = [ i for i in unranked if rankmatrix[i[0]][i[1]][rank-1][0] is None ]
		if WARN:
			print "At rank:" + str(rank) 
			print "self-ranks are:" + str(trace_at_rankN(rankmatrix, rank, teams))		
			print "Total self ranks:" + str(len(trace_at_rankN(rankmatrix, rank,teams)))
			print "Unranked " + str(len(unranked))
		#recursively sort within previous sort's topological equivalence classes
		topo_classes_by_rank.append([])
		needs_sorting=False
		for subclass in topo_classes_by_rank[rank-1]:
			#never try to resort a subclass with only one member!
			if len(subclass) < 2:
				topo_classes_by_rank[rank].append(subclass)
				continue
			dep_dict = {}
			build_dep_dict(subclass, rankmatrix, dep_dict, maxrank = 10000)
			try: #guard against cycles
				new_subclasses = [x for x in toposort2(dep_dict)]
				topo_classes_by_rank[rank].extend(new_subclasses)
				for x in new_subclasses:
					if len(x) > 1:
						needs_sorting=True
			except: #return original subclass unordered
				topo_classes_by_rank[rank].append(subclass)
				needs_sorting = True #trivially, as we didn't sort this one
		if INFO:
			print "*************** RANK{0}***************".format(rank)
			print '\n'.join(','.join(e for e in x) for x in topo_classes_by_rank[rank])
			print "**************************************"
	convexity(teams, rankmatrix)

	#Test topological sorts, return our best sort
	return topo_classes_by_rank[-1] 
	#need to do the lambda to bind the local rankmatrix var
	#return sorted(teams, lambda x, y: ordering(x,y,rankmatrix))	
	#return sorted(teams, anchored_ordering(rankmatrix, 'USA '))
	

identity = [(1,1)]*5
	



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
	counter = 0
	for eq_class in ranking:
		rank = 30 - counter
		#allow for draws correctly
		for team in eq_class:
			histo[team][rank] += 1
			counter = counter + 1
#	print ranking[29]
#	print histo[ranking[29]][29]

f = open('histo','w')
g = open('stats', 'w')
#h = open('num', 'w')
for n in teams:
	f.write(n + "," + ','.join([str(histo[n][i]) for i in range(1,lenteams+1)])+'\n') 
	mean = sum([histo[n][i]*i for i in range(lenteams+1)])/float(NUM)
	meansq = sum([histo[n][i]*i*i for i in range(lenteams+1)])/float(NUM)
	variance = meansq - mean*mean
	#the lenteams- adjusts for the backwards ranking
	g.write(n + "," + str(mean) + "," + str(variance) + '\n')

f.close()
g.close()

