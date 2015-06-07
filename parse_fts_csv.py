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

def safe_ratio(x,y):
	sx = max(1,float(x))
	sy = max(1,float(y))
	return sx/sy

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
		if species != "Travel Team" and species != "B Team" :
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

#name ordering stuff
def write_names(teams,names):
	tmp = open("names", 'w')
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
def output_matrices(bouts,names):
        A = [open('Avector','w'),open('Avector_test','w')]
        y = [open('yvector','w'),open('yvector_test','w')]
        W = [open('Wvector','w'),open('Wvector_test','w')]
        H = [open('Hvector','w'),open('Hvector_test','w')]
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

