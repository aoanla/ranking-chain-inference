# Licensed by aoanla under https://creativecommons.org/licenses/by-nc-sa/4.0/
import parse_fts_csv_2 as pfc
import time
import sys
import numpy as np
import scipy.optimize as optimize
import statsmodels.api as sm
import networkx
import cliques
from ztest import *
###parameters
##date limits

# Process for Python 2.2
#	does rankings the "hard way" - by iterating up the history chain generating splits where needed before getting around to actually making your ranking at the end
#


early_month = { "Jan":"Jan", "Feb":"Jan", "Mar":"Jan", "Apr":"Jan", "May":"Jan", "Jun":"Jan", "Jul":"Jul", "Aug":"Jul", "Sep":"Jul", "Oct":"Jul", "Nov":"Jul", "Dec":"Jul" }

ultimate_epoch_d = sys.argv[1].strip()
final_segs = ultimate_epoch_d.split('_')
f_ref_epoch_d = '01_' + early_month[final_segs[1]] + '_' + final_segs[2]

ultimate_epoch = time.mktime(time.strptime(ultimate_epoch_d, "%d_%b_%y"))   #end of sample training secords
f_ref_epoch = time.mktime(time.strptime(f_ref_epoch_d, "%d_%b_%y"))

#small Keener factor
N = 1

##source data
teamfile = "total_teams_2017-06-05.csv"
boutfiles = ["../flattrackstats_bouts_2017-06-05.csv",] 
tournamentfile = "../flattrackstats_tournaments_2017-06-05.csv"
###sequencing
##initialisation
teams_in = pfc.import_teams(teamfile)
tourns_in = pfc.import_tournaments(tournamentfile)
#tournament selection here is dependant on the host of the tournament actually being the host of the tournament, for long-running multi-venue tournaments.
#(the solution to this is to actually post-process FTS files and split up multiday tournaments into their component fixtures, or to fix FTS's internal data)
bouts_in = pfc.import_bouts(boutfiles,tourns_in,N) #Laplace/Keener perturbation is the second value. Probable sane values from 1 to 10.
#print len(bouts_in)
##selection
teams_winnowed = pfc.select_teams(teams_in,genuses=['W','M','C','J'])

#----------------------------------------------------------------------------------------------------------------------
#
#------------------------------------ GENERAL SETUP DONE --------------------------------------------------------------
#
#


# for each 6 month period from start to end: 
#	make reference for period
#		do divergences
#	move along 6 months
dates = []
stub = ["01_Jan_{0:02}","01_Jul_{0:02}"]
years = range(7,int(final_segs[2]))
for y in years:
	dates.append(time.mktime(time.strptime(stub[0].format(y), "%d_%b_%y")))
	dates.append(time.mktime(time.strptime(stub[1].format(y), "%d_%b_%y")))

Jandate = time.mktime(time.strptime(stub[0].format(int(final_segs[2])), "%d_%b_%y"))

dates.append(Jandate)

if Jandate != f_ref_epoch: #if we need July
	dates.append(f_ref_epoch)

dates.append(ultimate_epoch) #and the final date!

#when at the final reference period, do one final set, and output the final ratings

def model(la,hadv,weight):
        Ah = la['A'][0] - hadv * la['H'][0] #I *think* this is the right way around for home advantage adjustments
        W = np.exp(weight*la['W'][0]) #W is normalised time in the past (bigger with older), so weight should be -ve
        res = sm.WLS(la['Y'][0],Ah,W).fit()
        #res = sm.WLS(la['Y'][0],Ah,W).fit_regularized(L1_wt=0.0)  #fit (wls normal approach), fit_regularised(L1_wt=0 or 1 (ridge or lasso regression respectively), or a number between to weight them.
        return res

#current teams "lookup" for split teams (maps barename to most up to date name)
current_teams = {}
#--------------------------------- START LOOP

end_time = False

for date_i in range(1,len(dates)):
	datestart = dates[date_i] - 13*28*24*60*60 -  15634800.0
	datelim = dates[date_i-1]
	ref_epoch = dates[date_i-1]
	final_epoch = dates[date_i]
	print "Ref Epoch: {0}".format(ref_epoch)
	print "Target Epoch: {0}".format(final_epoch)
	
	#is this the last run?
	if date_i == (len(dates)-1):
		end_time = True

	#reference select
	(bouts_out,boutgraph,names) = pfc.select_bouts(bouts_in,teams_winnowed,datestart,ref_epoch,final_epoch)
	
	
	##subgraph selection
	
	#select largest subgraph
	subgraphs = pfc.process_subgraphs_2(boutgraph, teams_winnowed)
	smax = {}
	subgraphs.sort(reverse=True, key = len )
	
	
	#test(zip(op.params,op.bse), maximal_bouts[1], maximal_names)
	
	#we only do cliques for the biggest group, as many others are too small to bother
	sg0_cliques = None #confidences(subgraphs[0])
	
	#we now parallelise this over all subgraphs because we're insane and want to do rankings for the small groups too
	namerank = []
	
	for sg in subgraphs:
		(maximal_bouts, maximal_boutgraph, maximal_names) = pfc.select_bouts(bouts_in, sg, datestart, ref_epoch, final_epoch)
		#print sg
		
		la = pfc.output_numpy(maximal_bouts,maximal_names,comp='ratio')
	
	#Ratios
	#Optimised 2d params, via two different mechanisms, are hadv = -0.0439 , weight = -0.803
	# -1.64338301443 4.57569718514 (weight, z_lim) optimised via differential evolution [for 18 month total bout period start to end)
	# there's a weird variation in best weight,z_lim over the different dates we've tested. z_lim always > 4, weight between ~-1 to ~-1.8!
	# we're using -1.2, 4 here as a fairly conservative "mostly okay" default choice, although it's possible that polishing for each date might be better?
	#op = model(la,-0.0439,-0.803)
		op= model(la,-0.0410,-1.2)
		team_ref = { i[0]:[i[1],i[2]] for i in zip(maximal_names, op.params,op.bse) }
		team_z = test(team_ref,maximal_bouts[1],maximal_names, -0.0410)
		#z_print(team_z)
		#z_histogram(team_z)
		z_test(team_z, teams_winnowed, bouts_in, current_teams, ref_epoch, 4)

	#------------------------------- DIVERGENCES SPLIT

	#------------------------------- LOG STATE
	
	#for k in current_teams.keys():
	#	print '{0}|{1}'.format(k,current_teams[k])
	
	#------------------------------- RECALCULATE GRAPHS (if in final run - no point in previous runs)
	if (not end_time):
		continue
	print "Final Run"

	#expand to include test region
	(bouts_out,boutgraph,names) = pfc.select_bouts(bouts_in,teams_winnowed,datestart,final_epoch,0)
	
	##subgraph selection
	
	#select largest subgraph
	subgraphs = pfc.process_subgraphs_2(boutgraph, teams_winnowed)
	smax = {}
	subgraphs.sort(reverse=True, key = len )
	
	flag = end_time #only do confidences if we're on the end run, which is printed
	for sg in subgraphs:
	        (maximal_bouts, maximal_boutgraph, maximal_names) = pfc.select_bouts(bouts_in, sg, datestart, final_epoch, 0)
	        #print sg
	        #have to fix this so the graph is what confidences expects (should have 'kfactor' weighted edges)
	        if flag: #only bother with confidences if we're at the end run
	                sg0_cliques = cliques.confidences(maximal_boutgraph)
	                flag = False
	
	        la = pfc.output_numpy(maximal_bouts,maximal_names,comp='ratio')
	
	#Ratios
	#Optimised 2d params, via two different mechanisms, are hadv = -0.0439 , weight = -0.803
	#op = model(la,-0.0439,-0.803)
	        op= model(la,-0.0410,-1.2)
	        mx = max(op.params)
	        mean = np.mean(op.params)
	        stddev = np.std(op.params)
	        #"normalised" rating, mapped to a mean 0, stddev 1 distribution, for time series comparison
	        normal = (op.params - mean) / stddev

	#I don't think we can actually reasonably "zero" the distribution, given that hadv is a relative (fractional) contribution to both
	#and so "score" = s1*hadv - s2 -> if we shift by S, score = (s1-S)*hadv - (s2-S) = s1*hadv-s2 - S(hadv-1) 
		namerank.append(zip(maximal_names,op.params,op.bse, normal))

	#we sort each group internally, so that we can apply a ranking
	
	#post-process nameranks to remove "duplicate" teams after split
	for i in range(len(namerank)): 
		tmp = [] #new, filtered list
		for v in namerank[i]: #each team entry..
			if v[0][-3] != '_':
				basename = v[0] #determine basename
			else:
				basename = v[0][:-3]
			if basename not in current_teams: #has never been split so must be okay
				tmp.append(v)
			elif current_teams[basename] == v[0]:
				#current entry, include
				tt = (basename,v[1],v[2],v[3])
				tmp.append(tt)
				#tmp[-1][0] = basename #and fix name to basename
		namerank[i] = tmp #and replace with filtered list	
	
	if (end_time):
		f=open('{0}.out'.format(sys.argv[1]),'w')
		grp=0 #group id
		for group_ in namerank:
			group = sorted(group_, reverse=True, key=lambda x: x[1])
			counter=1
			for i in group:
				if grp == 1000:
					#we have subgroup info
					info = sg0_cliques[i[0]]
					clique_id = info['localpart']
					cliquity = int(10*info['local']/info['global'])/10.0
				else:
					clique_id = 0
					cliquity = 0
				string = "{0}|{1:d}|{2:d}|{3:.3f}|{4:.2f}|{5:.4f}|{6:.2f}|{7:d}".format(i[0],grp, clique_id,i[1],i[2],i[3],cliquity,counter)
				#string=str(i[0]) + '|' + str(grp) + '|' + str(clique_id) +'|'+ str(i[1]) + '|' + str(i[2]) + '|' + str(i[3]) + '|' + str(cliquity) + '|' + str(counter)
				#print string
				counter += 1
				f.write(string+'\n')
			grp += 1
		f.close()
