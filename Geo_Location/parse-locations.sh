#!/bin/bash

#expects a "uniform" format file
#outputs url-encoded names which match the cache
export PYTHONIOENCODING=utf-8
export LC_CTYPE=en_US.utf-8
export LC_ALL=en_US.utf-8
IFS=$'\n'; 
for i in `cat $1` 
	do 
		echo -n ${i%\"}'|'
		python quoter.py `cut -d'|' -f 6 <<<$i`
	 done
