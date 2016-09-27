# Licensed by aoanla under https://creativecommons.org/licenses/by-nc-sa/4.0/
import numpy as np
import emcee
import corner

#Utility function to build name list
namedict = {}
def namecheck(name, namedict):
	if name in namedict:
		return namedict[name]
	else:
		l = len(namedict)
		namedict[name] = l
		return l

#Read in input file, format:
#TEAM1 TEAM2 SCORE1 SCORE2
f = open("Champs-data")

#the teams
xdata = []
#the log score ratio
ydata = []

for l in f.readlines():
	lsplit = l.split()
	xdata.append((namecheck(lsplit[0],namedict),namecheck(lsplit[1],namedict)))
	ydata.append(np.log(float(lsplit[2])/float(lsplit[3])))

#log posterior function
#EMCEE is expecting this to be as [hypothetical real values = strengths], [measured input = teams at bout], [measured result = score ratio]
def log_posterior(theta, xdata, ydata):
	#reshape theta, for fixed param (strength of team 0 fixed at 1 to reduce dimensionality)
	#theta_int = list(theta)
	#our theta[-1] is "really" the sigma (we actually use -sigma so our limits are easier to specify wrt seeding values
	#sigma = theta[-1]
	#prior probs, constrain space to "reasonable" orders of magnitude of ability, variation
	#if sigma < -1.0:
	#	return -np.inf 
	#if sigma > 0.0:
	#	return -np.inf
	sigma = 0.2 #peak of distribution
	theta_int = list(theta)
	theta_int.append(0.0) #log 1 = 0
	for i in theta_int:
		if i < -2.0:
			return -np.inf
		if i > 0.5:
			return -np.inf
	#model is what we'd expect each result to be for the model scores
	y_model = [theta_int[xi[0]] - theta_int[xi[1]] for xi in xdata]
	#log probability is log RMS product of the probabilities of each result
	#which we can do more easily by summing the log probs 
	#theta[0] is the sigma for score distribution, assuming gaussian results
	#return -0.5 * np.sum(np.log(2*np.pi*sigma**2) + (ydata-y_model)**2/sigma**2)
	return -0.5 * np.sum([np.log(2*np.pi*sigma**2) + (y[0]-y[1])**2/sigma**2 for y in zip(ydata,y_model)])

#EMCEE stuff

#optimising wrt team strengths + sigma for "bout result variation"
#hypothetically, we should fix one team strength (with no loss of generality) to reduce dimensionality of problem to that of data
ndim = len(namedict)-1
nwalkers = 500
nburn = 3000
nsteps = 100000

np.random.seed(0)
starting_guesses = -1*np.random.random((nwalkers,ndim))

#sampler runs over hypotheticals, with acceptance from log_posterior probability
sampler = emcee.EnsembleSampler(nwalkers,ndim, log_posterior, args = [xdata, ydata] )

sampler.run_mcmc(starting_guesses, nsteps)

#remove burn-in steps, and make this just a set of samples (walkersxsteps)
emcee_trace = sampler.chain[:,nburn,:].reshape(-1, ndim)

#and then do some plotting stuff

names = [k for (k,v) in sorted(namedict.items(), key=lambda (k,v) : v)][:-1]
#replace last name, as this is actually sigma, as we fix the strength of team (MAX) = VRDL
#names[-1] = r'$\sigma$'

fig = corner.corner(emcee_trace, labels=names,show_titles=True)
fig.savefig("triangle.png")
