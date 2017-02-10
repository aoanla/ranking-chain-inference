# Licensed by aoanla under https://creativecommons.org/licenses/by-nc-sa/4.0/
import parse_fts_csv_2 as pfc
import time
import sys
import numpy as np
import scipy.optimize as optimize
import statsmodels.api as sm
###parameters
##date limits

datelim = time.mktime(time.strptime("01 Nov 16", "%d %b %y"))   #end of sample training secords
datestart = datelim - 12*28*24*60*60 # 9 months = time for largest stable group to form / minimum number of total connected groups to be reached with this dataset

datetest = datelim + 60*60*24*28*2 #1 month after datelim, end of testing records

N = 1
##source data
teamfile = "flattrackstats_teams_2016-12-02.csv"
#boutfiles = ["flattrackstats_bouts_2016-11-01.csv",
boutfiles = ["flattrackstats_bouts_2016-12-02.csv",] # "fts-additional-1.cvs", "fts-additional-2.cvs", "fts-additional-3.cvs", "fts-additional-4.cvs", "fts-additional-5.cvs", "fts-additional-6.cvs","fts-additional-7.cvs","fts-additional-8.cvs","fts-additional-9.cvs","fts-additional-10.cvs"]
tournamentfile = "flattrackstats_tournaments_2016-12-02.csv"
###sequencing
##initialisation
teams_in = pfc.import_teams(teamfile)
tourns_in = pfc.import_tournaments(tournamentfile)
#tournament selection here is dependant on the host of the tournament actually being the host of the tournament, for long-running multi-venue tournaments.
#(the solution to this is to actually post-process FTS files and split up multiday tournaments into their component fixtures, or to fix FTS's internal data)
bouts_in = pfc.import_bouts(boutfiles,tourns_in,N) #Laplace/Keener perturbation is the second value. Probable sane values from 1 to 10.
print len(bouts_in)
##selection
teams_winnowed = pfc.select_teams(teams_in,genuses=['W','M','C','J'])
(bouts_out,boutgraph,names) = pfc.select_bouts(bouts_in,teams_winnowed,datestart,datelim,datetest)

print len(bouts_out[0])

##subgraph selection

#select largest subgraph
subgraphs = pfc.process_subgraphs_2(boutgraph, teams_winnowed)
smax = {}
subgraphs.sort(reverse=True, key = len )

print "sub g"
print len(subgraphs[0])

# subgraphs[0] is now the dict of the teams in the largest group as id:{name,type etc} dict
(maximal_bouts, maximal_boutgraph, maximal_names) = pfc.select_bouts(bouts_in, subgraphs[0], datestart, datelim, datetest)
print "maximal"
print len(maximal_names)
print len(maximal_bouts[0])
print len(maximal_bouts[1])

##output the linear regression stuff
#pfc.write_names(subgraphs[0],maximal_names)

la = pfc.output_numpy(maximal_bouts,maximal_names,comp='ratio')

def model(la,hadv,weight):
	Ah = la['A'][0] - hadv * la['H'][0] #I *think* this is the right way around for home advantage adjustments
	W = np.exp(weight*la['W'][0]) #W is normalised time in the past (bigger with older), so weight should be -ve
	
	# or sm.WLS(la['Y'][0],Ah,W).fit() for standard weighted least squares (I don't see much difference to the values that regularisation gives, and it takes 10times longer to regularise)
	res = sm.WLS(la['Y'][0],Ah,W).fit()
	#res = sm.WLS(la['Y'][0],Ah,W).fit_regularized(L1_wt=0.0)  #fit (wls normal approach), fit_regularised(L1_wt=0 or 1 (ridge or lasso regression respectively), or a number between to weight them.
	#print student
	return res

#op = model(la,0.11,-1.0)

#call with ranks = op[0]
def estimate(ranks,la, hadv):
        Ah = la['A'][1] + hadv * la['H'][1]
        est = np.dot(Ah,ranks)
        diff = la['Y'][1] - est
        return sum([d*d for d in diff]) #sum of squares

#This was bug-testing - we were letting teams into the tester which were not in the training data (and thus had "random" ranks which could be v large!)
#print [(teams_winnowed[i[0]][0],i[1]) for i in zip(maximal_names,op[0]) if abs(i[1])>20]
#print [(teams_winnowed[i[0]][0],i[1],i[2]) for i in zip(maximal_names,la['A'][1][-2],op[0]) if i[1]!=0]
#sys.exit(1)
#value = estimate(op[0],la,0.11)


#print op
#print "Prediction (sum of squared errors)"
#print value

# From the old evaluator, for reference
#(od,maximal_names,maximal_bouts,subgraph) = pfc.predict(datelim,predict_window,eval_window,bouts_in, teams_winnowed)
#calculate prediction for evaluation frame
#name_divergences = pfc.estimate(od,maximal_names,maximal_bouts)
def predict(datelim,predict_window,eval_window,bouts_in, teams_winnowed, hadv, weight):
	(bouts_out,boutgraph,names) = pfc.select_bouts(bouts_in,teams_winnowed,datestart,datelim,datetest)
	subgraphs = pfc.process_subgraphs_2(boutgraph, teams_winnowed)
	subgraphs.sort(reverse=True, key = len )
	(maximal_bouts, maximal_boutgraph, maximal_names) = pfc.select_bouts(bouts_in, subgraphs[0], datestart, datelim, datetest)
	la = pfc.output_numpy(maximal_bouts,maximal_names)
	return (la,model(la,hadv,weight))

#this is the estimator which returns individual divergences, for the splitter (estimate function instead returns a *score*, for the minimiser)
def estimator(ranks,la, hadv):
	Ah = la['A'][1] + hadv * la['H'][1]
        est = np.dot(Ah,ranks)
        diff = la['Y'][1] - est
	divergences = np.dot(np.transpose(la['A'][1]),diff)
	return divergences
	# we need to return a matrix of divergences [that is, assign these errors to the ranks in question]
        #return sum([d*d for d in diff]) #sum of squares



bounds_list=([-1,1],[-3,0.1])

#diff_evo suggests hadv = 0.07418
# but looser dep on weight (get v different values with same resulting errors)
def ranker_harness(params,la,presets={}):
	unset = [True,True]
	if presets != {}:
		if 'hadv' in presets:
			hadv = preset['hadv']
			unset[0] = False
		if 'weight' in presets:
			weight = preset['weight']
			unset[1] = False
	idx = 0
	if unset[0]: 
		hadv=params[idx]
		idx+=1
	if unset[1]:
		weight=params[idx]
		idx+=1
	#cutoff=params[2] 
	op = model(la,hadv,weight)
	return estimate(op.params,la,hadv)

#f = open("graph.out",'w')
#def make_range(mi,mx,stp):
#	stps = int((mx-mi)/stp)
#	return [ mi+i*stp for i in range(stps)]
#for i in make_range(-3,-0.1,0.05):
#	f.write("%f %f\n" % (i,ranker_harness((0.07418,i),la)))
#f.close()
#res = optimize.minimize(ranker_harness,[-0.1,-0.5],method="TNC",args=(la,),bounds=bounds_list)
#res = optimize.differential_evolution(ranker_harness,bounds_list,args=(la,))

#print res
#
#print "Optimised Params"
#print res.x


#Ratios
#Optimised 2d params, via two different mechanisms, are hadv = -0.0439 , weight = -0.803
#op = model(la,-0.0439,-0.803)

#Diffs
#Optimised 2d params, via two different mechanisms, are [-0.04104377 -0.39339671]
#which suggests hadv is generic; weight here might be influenced by our "30 minute tournament games issue"
op= model(la,-0.0410,-0.393)
mx = max(op.params)

print op.summary()

rnk = [mx-opi for opi in op.params]

#I don't think we can actually reasonably "zero" the distribution, given that hadv is a relative (fractional) contribution to both
#and so "score" = s1*hadv - s2 -> if we shift by S, score = (s1-S)*hadv - (s2-S) = s1*hadv-s2 - S(hadv-1) 
namerank = zip(maximal_names,op.params,op.bse)

ranking = sorted(namerank,lambda x,y: cmp(x[1],y[1]))
print "Rank Name Ln(str) MSE(ln(str))"
for i in zip(range(1,len(ranking)+1),ranking):
	print str(i[0]) + ' ' + teams_winnowed[i[1][0]][0] + ' ' + str(i[1][1]) + ' ' + str(i[1][2])
#print [teams_winnowed[i[0]][0] for i in sorted(namerank,lambda x,y: cmp(x[1],y[1]))]










#ratiosort = [ ) for i in  sorted(combined, lambda x,y: cmp(y[1][1],x[1][1])) 
