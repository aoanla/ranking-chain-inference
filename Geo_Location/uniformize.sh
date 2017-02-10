#!/bin/bash
tr -d $'\r' <$1 | sed 's/^"//;s/","/|/g;s/"//' > ${1%.csv}.uniform
