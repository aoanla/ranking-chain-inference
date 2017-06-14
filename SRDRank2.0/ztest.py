# Licensed by aoanla under https://creativecommons.org/licenses/by-nc-sa/4.0/
import sys
import numpy as np
###parameters
##date limits


#test(zip(op.params,op.bse), maximal_bouts[1], maximal_names)
def test(team_ref, test_bouts, names, hadv):
	team_z = { t:{} for t in names }
	n = team_ref.keys()
	for b in test_bouts:
		if b[0] not in n or b[1] not in n:
			continue
		result = b[3] #hadv correction in next line from b[4]
		if b[4] != 1: #do this right later
			hadv = 0 
		prediction = team_ref[b[0]][0] * (1-hadv) - team_ref[b[1]][0]
		stdev = team_ref[b[0]][1] + team_ref[b[1]][1]
		error = (result - prediction) / stdev
		team_z[b[0]][b[1]] = error #+ve for team1? 
		team_z[b[1]][b[0]] = -error
	return team_z
#z value

def div_test(team_ref, test_bouts, names, hadv):
        n = team_ref.keys()
	vect = []
        for b in test_bouts:
                if b[0] not in n or b[1] not in n:
                        continue
                result = b[3] #hadv correction in next line from b[4]
                if b[4] != 1: #do this right later
                        hadv = 0
                prediction = team_ref[b[0]][0] * (1-hadv) - team_ref[b[1]][0]
		vect.append(result-prediction)
        return vect



#z_lim = 3  say - this is pretty high, and corresponds to about 1/1000 chance of natural variation

def z_sum(team_list):
	if len(team_list.values()) < 2: #don't split things with zero or 1 result
		return 0
	return sum(team_list.values())/np.sqrt(len(team_list.values()))

def z_histogram(team_z):
	tmp = {}
	for t in team_z.keys():
		h = z_sum(team_z[t])
		if h != 0:
			q_h = 0.5*int(h*2) #quantize to 0.5s
			if q_h not in tmp:
				tmp[q_h] = 0
			tmp[q_h] = tmp[q_h] + 1
	for k in tmp:
		print u"{0} {1}".format(k, tmp[k])

def z_print(team_z):
	for t in team_z.keys():
		#print u"{0} {1} {2}".format(t,z_sum(team_z[t]), team_z[t] )
		print u"{0} {1}".format(t,z_sum(team_z[t]))

#team list is global team list, something like teams_winnowed
#current_teams is a quick lookup for the basename of a team for the "modern" version of it
#bouts is a global bouts list, something like bouts_in
def z_test(team_z,team_list,bouts, current_teams, ref_epoch, z_lim=3):
	teams = team_z.keys()
	flag = True
	#while we keep finding anomalies
	while(flag):
		#sort by z value - need biggest thing at the top
		m_team = max(teams, key=lambda t: abs(z_sum(team_z[t])) )
		#
		if abs(z_sum(team_z[m_team])) > z_lim:
			#split m_team
			#print "Splitting off: {0} with deviation {1}".format(m_team,z_sum(team_z[m_team]))
			if m_team[-3] == '_': #split before
				new_team = m_team[:-2] + '{0:02}'.format(int(m_team[-2:])+1)
				current_teams[m_team[:-3]] = new_team
			else:
				new_team = m_team+'_00'
				current_teams[m_team] = new_team
			team_list[new_team] = team_list[m_team]
			for k in bouts.keys(): #k is a *time*
				if k > ref_epoch: #fair game for splitting if time more recent than test epoch
					tmp = []
					for b in bouts[k]: #for all bouts on this date: 			
						#update to the new team
						bb = [b[0],b[1]]
						if b[0] == m_team:
							bb[0] = new_team
						if b[1] == m_team:
							bb[1] = new_team
						tmp.append((bb[0],bb[1],b[2],b[3],b[4]))
					bouts[k] = tmp
			#remove m_team contribs from others
			for t in teams:
				if m_team in team_z[t]:
					del team_z[t][m_team]
			#and itself
			del team_z[m_team]
			teams = team_z.keys()
		else:
			flag = False

#test(zip(op.params,op.bse), maximal_bouts[1], maximal_names)
