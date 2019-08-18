# -*- coding: utf-8 -*-
'''
This script takes the input NewsScape file and extracts the relevant text from it.
'''
from datetime import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument( '--input_file', type=str, help='Name of\
                    input file',default='2019-01-21_0410_CN_HNTV1_午间新闻.txt')
parser.add_argument( '--timing', default=1, type=int, help="Option to decide whether\
                    to include timing info in output")
args = parser.parse_args()

with open(args.input_file) as f:
	content = f.readlines()
content = [x.strip() for x in content]

date_format = "%Y%m%d%H%M%S.%f"
fields = set(["TOP", "COL", "UID", "PID", "ACQ", "DUR", "VID", "TTL", "URL", "TTS", "SRC", "CMT", "LAN", "TTP", "HED", "OBT", "LBT", "END", "CC1","ASR_01"])
text = ''
for line in content:
	l = line.split('|')
	if l[0]=="TOP":
		start = datetime.strptime(l[1]+'.0', date_format)
	elif l[0]=="END":
		break
	elif l[0] not in fields:
		t = datetime.strptime(l[0], date_format)
		s = l[-1]
		#print s
		if args.timing:
			text+=' '.join(['S_'+str(int((t-start).total_seconds())),s,''])
		else:
			text+=' '.join([s,''])
print text
with open("preprocess.txt", "wb") as f:
    f.write(text)
