import math
histf = open('histo','r')
statf = open('stats','r')

histdict = {}
statdict = {}
names = []
maxfreq = 0
for l in histf:
	ls = l.split(',')
	nums = [ float(i) for i in ls[1:]]
	for i in nums:
		maxfreq = maxfreq if (maxfreq > i) else i
	histdict[ls[0]] =  nums
	names.append(ls[0])

histf.close()

#rescale to 1.0
for n in names:
	tmp = histdict[n]
	histdict[n] = [ i/maxfreq for i in tmp]


for l in statf:
	ls = l.split(',')
	statdict[ls[0]] = [float(ls[1]), float(ls[2])]

statf.close()
#print histdict
print statdict

snames = sorted(names, lambda x,y: cmp(statdict[x][0],statdict[y][0]))

stringify = lambda numlist:''.join(["<td>{:02d}</td>".format(i) for i in numlist])
colormap = lambda val: "#"+hex(int(255*val))[2:]*3
colourify = lambda numlist:''.join(["<td bgcolor="+colormap(i)+"></td>" for i in numlist])
variance = [ statdict[i][1] for i in snames]
#alert = lambda val: "#FFFFFF"
alert = lambda val: "#"+hex(255-min(255,int(4*math.sqrt(val))))+"FFFF"

op = open('heatmap','w')
op.write("<table>"+'\n')
op.write("<tr><td></td>"+stringify(range(1,len(names)+1))+"</tr>"+'\n')
for n in zip(snames, range(1,len(names)+1), variance):
	op.write("<tr><td bgcolor="+alert(n[2])+">" + str(n[1]) + ". " + n[0] +"</td>"+colourify(histdict[n[0]])+"</tr>"+'\n')

op.write("</table>"+'\n')

op.close()

