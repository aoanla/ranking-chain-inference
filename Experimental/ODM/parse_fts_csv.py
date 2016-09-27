# Licensed by aoanla under https://creativecommons.org/licenses/by-nc-sa/4.0/
import time
import math
import networkx
import matplotlib
import matplotlib.pyplot as plt
import unicodedata as ud
import numpy as np
import ODM as sk

matplotlib.rc('text',usetex=False)
#TODO:
#
# Graph connectivity analysis -> we can't rank a disconnected graph of teams!
#

def safe_ratio(x,y):
	sx = max(1,float(x))
	sy = max(1,float(y))
	return sx/sy

def safe_log_ratio(x,y):
	return math.log(safe_ratio(x,y))

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

def import_bouts(boutfile):
	b = open(boutfile, 'r')
        b.readline()

        bouts = dict()

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
                scorerat = math.log(safe_ratio(scores[0],scores[1]))
		
		if date not in bouts:
			bouts[date] = list()

                bouts[date].append((ts[0], ts[1], scorediff, scorerat, tourn))
        b.close()
        return bouts

def import_bouts_raw(boutfile):
        b = open(boutfile, 'r')
        b.readline()

        bouts = dict()

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

                if date not in bouts:
                        bouts[date] = list()

                bouts[date].append((ts[0], ts[1], scores[0], scores[1], tourn))
        b.close()
        return bouts



def select_bouts(bouts,teamlist,startdate,enddate,trainingperiod):
	
	bouts_out = (list(),list())
	
	#graph of all team v team connections via bouts
	#to avoid double-counting, we strictly order by alphabetical sorting.
	#that is A-B and B-A both stored as [A][B] = 1, D-C as [C][D] = 1
	boutgraph = networkx.Graph()
	
	names = set()
	duration = 9*28*24*60*60*1.0 #9 month normalisation (9 months old = 1.0 units old)
	
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
			bouts_out[selector].append((vv[0], vv[1], vv[2], vv[3], (enddate-k)/duration, vv[4]))
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

#do subgraph analysis

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

#implement Govan's Offense-Defence model
#Current defaults are mse optimised values for 9 month period ending 6 May 2016
# mse optimised hadv is almost always close to 0.96
# mse optimised recency varies quite a lot, usually in range -2.5 to -1 (-1 most common end)
# but, for ex 'W' only cohort, 9months to 6 May 2016 has -5!
def odm(bouts, names, hadv=0.96, recency=-5.0):
	a = np.zeros((len(names),len(names))) #score array
	teamfreq = np.zeros(len(names))
	tindex = dict()
	for i,t in zip(range(len(names)),names):
		tindex[t] = i

	for b in bouts[0]: #bouts[0] is training data, bouts[1] is test data!
		homefactor = 1 if b[5]==0 else hadv
		id0 = tindex[b[0]]
		id1 = tindex[b[1]]
		#increase our running total of bouts per team
		teamfreq[id0] += 1
		teamfreq[id1] += 1
		#can include recency based on value in b[4], but most useful for weighted sums
		#we need some way to account for multiple bouts per pair existing!
		a[id0,id1] = (b[3] / homefactor)*math.exp(recency*b[4]) #I think - a[i][j] is j's score against i
		a[id1,id0] = (b[2] *homefactor)*math.exp(recency*b[4]) # so b[3] is score[1] not score[0] etc
	
	#tweak to force the matrix to have total support - tiny fudge factor to all elements (Govan's PhD thesis suggests tiny values sufficient
	# and the smaller the value the smaller the decrease in predictive accuracy - she uses 1e-5 so that seems a good place)
	a+=0.00001

	sksolv = sk.SinkhornKnopp()
	od = sksolv.fit( a , teamfreq)
	#normalisaton needed in fit above 
	#scores = o/d #elementwise!
	return od

#test against training data
# we might assume that the ratio of power rating is proportional to the ratio of scores?

#scipy.optimize.minimize(mse_predictor,[hta,recency],[maximal_bouts,maximal_names]):
#scipy.optimize.minimize(odm_train,[1,0],args = (maximal_bouts,maximal_names))

def odm_train(values,bouts,names):
        hta = values[0]
	loghta = math.log(hta)
	#hta = 0.96
	# recency varies much more - seems to generally be around -2.5 to -1, depending on the range and start time
	# significant outlier for 6 May 2016 , 9 month period, which gives -4.5 or -5!
        recency = values[1] #values[0]
        #maximal_bouts = args[0]
        #maximal_names = args[1]
        a = np.zeros((len(names),len(names))) #score array
        teamfreq = np.zeros(len(names))
        tindex = dict()
        for i,t in zip(range(len(names)),names):
                tindex[t] = i

        for b in bouts[0]: #bouts[0] is training data, bouts[1] is test data!
                homefactor = 1 if b[5]==0 else hta
                id0 = tindex[b[0]]
                id1 = tindex[b[1]]
                #increase our running total of bouts per team
                teamfreq[id0] += 1
                teamfreq[id1] += 1
                #can include recency based on value in b[4], but most useful for weighted sums
                #we need some way to account for multiple bouts per pair existing!
                a[id0,id1] += (b[3] / homefactor)*math.exp(recency*b[4]) #I think - a[i][j] is j's score against i
                a[id1,id0] += (b[2] *homefactor)*math.exp(recency*b[4]) # so b[3] is score[1] not score[0] etc

        #tweak to force the matrix to have total support - tiny fudge factor to all elements (Govan's PhD thesis suggests tiny values sufficient
        # and the smaller the value the smaller the decrease in predictive accuracy - she uses 1e-5 so that seems a good place)
        a+=0.00001

        sksolv = sk.SinkhornKnopp()
        od = sksolv.fit( a , teamfreq)
        #assumes np has a log which distributes
        logstr = [ lodi[0] - lodi[1] for lodi in np.log(od)]
        mse = 0
        for b in bouts[1]:
		loghf = 0 if b[5]==0 else loghta
                actual_ratio = safe_log_ratio(b[2],b[3])+2*loghf #== applying hta appropriately
                #smaller "strength" seems better?
                #uses tindex, so should be in pfc
                predicted_ratio = logstr[tindex[b[1]]] - logstr[tindex[b[0]]]
                mse += (actual_ratio - predicted_ratio)**2
        return mse

def odm_train1(values,bouts,names): #hack for fixing hta
	return odm_train([0.96,values[0]],bouts,names)
