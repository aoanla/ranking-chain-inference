import sys
f = open(sys.argv[1])
fll = [fli.strip().split('|') for fli in f.readlines()]
f.close()
f =  open('fts-teams_2016-11-01.denormalised')
tll = [tli.strip().split('|') for tli in f.readlines()]
tlldict = {i[0]:":".join(i[1:3]) for i in tll[1:]}
f.close()
f = open(sys.argv[1]+"fill",'w')
for flli in fll:
	print flli[0] + '  ' + flli[1] + '  ' + tlldict[flli[4]] + '  ' + tlldict[flli[6]]
	values = raw_input()
	if values[0] == 'X':
		continue #skip this line and remove from output file
	elif values[0] == 'S':
		pass #output line, but not filled in
	elif values[0] == "Q":
		sys.exit()
	else:
		v = values.strip().split(':')
		flli[5] = v[0]
		flli[7] = v[1]	
	f.write('|'.join(flli) + '\n')
f.close()
