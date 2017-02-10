# Licensed by aoanla under https://creativecommons.org/licenses/by-nc-sa/4.0/
import time
import math
import networkx
import matplotlib
import matplotlib.pyplot as plt
import unicodedata as ud

matplotlib.rc('text',usetex=False)
#TODO:
#
# Graph connectivity analysis -> we can't rank a disconnected graph of teams!
#

#N is an additive perturbation to the scores, applied before ratio is taken
#Motivation is Keener direct ratings, which do something similar,
#but we use them specifically to avoid the singularity at 0, while tuning the
#strength factors gained per (opposition point prevented) for low opposition scores.
def safe_ratio(x,y,N=0):
	sx = max(1,float(x)+N)
	sy = max(1,float(y)+N)
	return sx/sy

def import_rankings(rankingfile):
	t = open(rankingfile, 'r')
	
	#print l.split(',')
	teams = dict()
	#genus = set()
	#domain = set()
	for line in t:
		items = line.decode('utf_8').encode('ascii','ignore').split(',')
		if items[0][0] != '(':
			#print items[0]
			continue
		
		#need to strip off the double quotes surrounding each item...
		#and remove non-ascii chars for plotter
		try:
			name = items[0][2:-1]
			rank = items[1][:-1]
			teams[name] = rank
		except:
			pass
		
	return teams

def import_teams(teamfile):
	t = open(teamfile, 'r')
	
	#read header out first
	l = t.readline()
	#print l.split(',')
	teams = dict()
	#genus = set()
	#domain = set()
	for line in t:
		items = line.decode('utf_8').encode('ascii','ignore').split('","')
		#need to strip off the double quotes surrounding each item...
		#and remove non-ascii chars for plotter
		name = items[1]
		#name = ud.normalize('NFKD',items[1][1:-1]).encode('ascii','ignore').replace(" ", "_")
		#W M C J
		genus = items[-2][0]
		#Europe USA Canada Australia New Zealand Pacific ""
		domain = items[-1].strip()[:-1]
		species = items[4]
		#for example, filter on Women's Teams
	#	if genus != "C":
	#		continue
		#and filter on only Travel / B teams
		if species != "Travel Team" and species != "B Team": 
			continue
		teams[items[0][1:]] = (name, domain, genus)
		#domain.add(items[-1][1:-3])
		#genus.add(items[-2][1:-1])
	
	t.close()
	return teams
	
def select_teams(teams,domains=['Europe','USA','Canada','Australia','New Zealand','Pacific',''],genuses=['W','M','J','C']):
	return {t:v for (t,v) in teams.iteritems() if v[1] in domains and v[2] in genuses}

#Laplace/Keener perturbation N here - ugly functionally, but without making a class, the best place to apply it
def import_bouts(boutfiles,N=0):
	bouts = dict()
	
	for boutfile in boutfiles:
		b = open(boutfile, 'r')
       		b.readline()
		
	
        	for line in b:
                	items = line.split(',')
                	date = time.mktime(time.strptime(items[1],'"%Y-%m-%d"')) #seconds since epoch of bout happening    line[1]
 			tourn = 1
			if items[3] != '""': #there's a tournament specified
                	        tourn = 0
                	ts = (items[4][1:-1],items[6][1:-1])
                	#no scores - no data
                	if items[5] == '""':
                	        continue
                	scores = (int(items[5][1:-1]), int(items[7].strip()[1:-1]))
                	scorediff = scores[0] - scores[1]
                	scorerat = math.log(safe_ratio(scores[0],scores[1],N))
			
			if date not in bouts:
				bouts[date] = list()
	
                	bouts[date].append((ts[0], ts[1], (scores[0],scores[1]), scorerat, tourn))
        	b.close()
        return bouts



def select_bouts(bouts,teamlist,startdate,enddate,trainingperiod):
	
	bouts_out = (list(),list())
	
	#graph of all team v team connections via bouts
	#to avoid double-counting, we strictly order by alphabetical sorting.
	#that is A-B and B-A both stored as [A][B] = 1, D-C as [C][D] = 1
	boutgraph = networkx.Graph()
	
	names = set()
	
	
	for (k,v) in bouts.iteritems(): 
		selector = 0
		if (k < startdate):
			continue
		elif (k > enddate):
			if (k > trainingperiod):
				continue
			selector=1 #testing
		#for all bouts for this date:
		for vv in v: 
			if (vv[0] not in teamlist) or (vv[1] not in teamlist):
				continue			
			#names list (for teams featured in a bout in our window - use this to prune teams dict)
			names.add(vv[0])
			names.add(vv[1])
			#boutgraph increment
			boutgraph.add_edge(vv[0],vv[1])
			#ordered_add(boutgraph,ts[0],ts[1])
			#score calc	
			bouts_out[selector].append((vv[0], vv[1], vv[2], vv[3], enddate-k, vv[4]))
	return (bouts_out,boutgraph,names)


def select_bouts_teamdict(bouts,teamlist,startdate,enddate,trainingperiod):
	
	bouts_out = (list(),list())
	
	#graph of all team v team connections via bouts
	#to avoid double-counting, we strictly order by alphabetical sorting.
	#that is A-B and B-A both stored as [A][B] = 1, D-C as [C][D] = 1
	boutgraph = networkx.Graph()
	
	names = set()
	
	
	for (k,v) in bouts.iteritems(): 
		selector = 0
		if (k < startdate):
			continue
		elif (k > enddate):
			if (k > trainingperiod):
				continue
			selector=1 #testing
		#for all bouts for this date:
		for vv in v:
			#select teams which are not in the same dict in teamlist dict
			keys = teamlist.keys()
			fail = 1
			for key in keys:
				if vv[0] not in teamlist[key]:
					continue
				if vv[1] in teamlist[key]:
					fail = 1		
					break
				keys2 = [ktmp for ktmp in keys if ktmp != key]
				if vv[1] not in [v for key2 in keys2 for v in teamlist[key2]]:
						fail = 1
						break #vv[1] is in diff key class as vv[0], but in some key class
				fail=0
				break 
			if fail==1:
				continue			
			#names list (for teams featured in a bout in our window - use this to prune teams dict)
			names.add(vv[0])
			names.add(vv[1])
			#boutgraph increment
			boutgraph.add_edge(vv[0],vv[1])
			#ordered_add(boutgraph,ts[0],ts[1])
			#score calc	
			bouts_out[selector].append((vv[0], vv[1], vv[2], vv[3], enddate-k, vv[4]))
	return (bouts_out,boutgraph,names)


#Weighted graphs:
def select_bouts_weighted(bouts,teamlist,startdate,enddate,trainingperiod,weight='ratio',bidir=True):

        bouts_out = (list(),list())

        #graph of all team v team connections via bouts
        #to avoid double-counting, we strictly order by alphabetical sorting.
        #that is A-B and B-A both stored as [A][B] = 1, D-C as [C][D] = 1
        boutgraph = networkx.DiGraph() if bidir else networkx.Graph() #or DiGraph if we're directed
	datenormalise = 9*28*24*60*60 #normalise to 9 months
        names = set()
	htacorr = 1
	htafun = lambda x,y: x
	component = 3
	if weight == 'ratio':
		htacorr = math.log(0.92) #empirically determined home team advantage correction from previous studies
		component = 3
		htafun = lambda x,y: x+y
		null = 0
	elif weight == 'diff':
		htacorr = 0.96 #for scorediff - sqrt(0.92), because the ratio applies it twice (once to numerator, once to denominator)
		component = 2
		htafun = lambda x,y: (x[0]*y - x[1]/y) 
		null = 1
        for (k,v) in bouts.iteritems():
                selector = 0
                if (k < startdate):
                        continue
                elif (k > enddate):
                        if (k > trainingperiod):
                                continue
                        selector=1 #testing
                #for all bouts for this date:
                for vv in v:
                        if (vv[0] not in teamlist) or (vv[1] not in teamlist):
                                continue
                        #names list (for teams featured in a bout in our window - use this to prune teams dict)
                        names.add(vv[0])
                        names.add(vv[1])
			# - can add edge weight by either signed (and assuming A-B ordering), or as a directed edge (winner -> loser)
                        #boutgraph increment - scorerat is vv[3] for a boutlist from non-raw import
                        #if boutgraph.has_edge(vv[0],vv[1]):
			#	boutgraph.remove_edge(vv[0],vv[1])
			#	if bidir:
			#		boutgraph.remove_edge(vv[1],vv[0])
			#boutgraph.add_edge(vv[0],vv[1], weight = abs(math.log(vv[3])) )
                        #ordered_add(boutgraph,ts[0],ts[1])
			#directed graph:
			w = htacorr if vv[4]==0 else null #no correction if a tournament, as neutral court assumed [this is not always true, but it's harder to prove this with FTS data]
			wcorr = htafun(vv[component], w) #vv[2] * w #or vv[3] + w for scorerat (vv[2] * w for score diff)
			boutgraph.add_edge( vv[0],vv[1],weight = (wcorr),kfactor=(enddate-k)/datenormalise )
			if bidir:
				boutgraph.add_edge(vv[1],vv[0],weight = -(wcorr),kfactor=(enddate-k)/datenormalise )
                        #score calc     
                        bouts_out[selector].append((vv[0], vv[1], vv[2], vv[3], enddate-k, vv[4]))
        return (bouts_out,boutgraph,names)



#do subgraph analysis


#Reasoning 17Jun idea for "geometric" ordering based on plotting link-length by scoreratio/scoreratio equiv class needs modification of process-graph to implement
def process_graph(g,text,teams, colour_map):
        print text
	#approximate scaling law for good plot size
	scale = math.log(len(g.nodes()))
	p_dim = max(scale*scale,1)+3                
	plt.figure(1,(p_dim,p_dim))
        node_labels = dict([ (n,teams[n][0]) for n in g.nodes() ])
        node_cols = [ colour_map[teams[n][1]] for n in g.nodes() ] 
	pos = networkx.spring_layout(g)
	networkx.draw_networkx_nodes(g,pos,node_size=1000,node_color=node_cols)

	networkx.draw_networkx_edges(g,pos)
	networkx.draw_networkx_labels(g,pos,labels = node_labels)
#        networkx.draw_spring(g,with_labels=True, node_color=node_cols, labels = node_labels)
        plt.savefig(text+".png")
        plt.close()
        for gv in g:
                print gv
        print
        print

#process_graph(boutgraph,"AllGroups")
def process_subgraphs(g, teams):
	subgraphs = networkx.connected_component_subgraphs(g)
	colour_map = { 'USA':'r', 'Europe':'g', 'Canada':'b', 'Australia':'c', 'New Zealand':'m' ,'Pacific':'y' , '':'w' }
	i = 1
	team_groups = list()

	for s in subgraphs: #a list of teams in each connected subgraph
		n_str = "Group " + str(i)
		process_graph(s,n_str, teams, colour_map)
		i = i+1

#output winnowed team lists, per connected group
def process_subgraphs_2(g, teams):
	subgraphs = networkx.connected_component_subgraphs(g)
	team_groups = list()
	for s in subgraphs:
		team_groups.append({n:teams[n] for n in s.nodes() })
	return team_groups

#do the above, but for directed graphs (via an undirected proxy, as the subgraph stuff isn't implemented for general digraphs)
def process_subgraphs_2_directed(g,teams):
	tmpg = g.to_undirected()
	tmpsubgs = process_subgraphs_2(tmpg,teams)
	#we also fix this so we actually return the bloody subgraphs, not a dict
	subgs = [g.subgraph(sgi.keys()) for sgi in tmpsubgs ]
	return subgs
	
#name ordering stuff
def write_names(teams,names, prefix = ""):
	tmp = open(prefix + "names", 'w')
	for v in names:
		tmp.write(teams[v][0]+'\n')
	tmp.close()
	
#OUTPUT VALUES

#utility function to get the right elements in A (inefficient but data is more efficient in memory)
def n_win(l,n):
	if l[0]==n:
		return 1
	if l[1]==n:
		return -1
	return 0

#returns the home advantage colum for the line in H (which is just the "home teams" column in A)
def h_adv(l,n):
	#if it's a tournament no home advantage
	if l[5]==0:
		return 0
	#l[0] is always the home team, and always +1 (l[1] is -1)
	if l[0]==n:
		return 1
	return 0

#output the linear regression matrices for these bouts
def output_matrices(bouts,names, prefix = ""):
        A = [open(prefix + 'Avector','w'),open(prefix + 'Avector_test','w')]
        y = [open(prefix + 'yvector','w'),open(prefix + 'yvector_test','w')]
        W = [open(prefix + 'Wvector','w'),open(prefix + 'Wvector_test','w')]
        H = [open(prefix + 'Hvector','w'),open(prefix + 'Hvector_test','w')]
        for i in range(2):
                for line in bouts[i]:
                        #y is a 2 column result vector for scorediff and scoreratio respectively
                        y[i].write(str(line[2])+' '+str(line[3])+' '+'\n')
                        #W is the vector of dates (before the most recent record), for record optimisation
                        W[i].write(str(line[4])+'\n')
                        #A is a n-column team matrix for each line in the simultaneous equations
                        Aline = ' '.join([ str(n_win(line,n)) for n in names ])
                        A[i].write(Aline+'\n')
                        #H is a n-column team matrix for each line, giving the home team advantage marker
                        Hline = ' '.join([ str(h_adv(line,n)) for n in names ])
                        H[i].write(Hline+'\n')
                H[i].close()
                W[i].close()
                A[i].close()
                y[i].close()

