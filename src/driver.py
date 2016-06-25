#!/usr/bin/python

import subprocess, sys, json

latte = open(sys.argv[1]).readlines()
func_params, func_ranges = latte[0].strip().split('<'), []
start, end, capture_start = latte[2:][0].split()[0], None, False
for line in latte[2:]:
	if capture_start:
		start = line.split()[0]
		capture_start = False
	if not line.startswith('probabilities'):
		end = line.split()[0]
	else:
		capture_start = True
		func_ranges.append((start, end))

params = ["./yara", "-a"]
params.extend(sys.argv[2:])

for index in range(len(func_params)):
	params.extend([func_params[index].strip() + '=[-' + func_ranges[index][0].strip() + ',' + func_ranges[index][1].strip() + ']'])

data = open(sys.argv[2], 'r').read()
if data.find('float') != -1 or data.find('double')!= -1:
	exit()

limits, key = None, None
start_capturing = False
ranges = {}

proc = subprocess.Popen(params, stdout=subprocess.PIPE)
while True:
	line = proc.stdout.readline()
	if line != '':
		if not line.strip():
			continue
		if line.startswith('In the following result'):
			limits = [int([v.strip() for v in r.strip().split('=')][1]) for r in line.replace('In the following result', '').strip().split('&')]
		if line.startswith('Reached fixed point after'):
			start_capturing = True
			continue
		if start_capturing:
			if line.find('(line #') != -1:
				key = int(line.split('(line #')[-1].strip()[:-3])
				ranges[key] = {}
			else:
				values = line.strip().split('=')
				values[1] = values[1].replace('m', str(limits[0])).replace('M', str(limits[1]))
				ranges[key][values[0]] = json.loads(values[1])
	else:
		break

for k, v in ranges.items():
	text = ''
	for var, interval in v.items():
		if interval:
			text += '  assume(' + var + ' >= ' + str(interval[0]) + ');\n'
			text += '  assume(' + var + ' <= ' + str(interval[1]) + ');\n'
	ranges[k] = text

inFile = open(sys.argv[2], 'r')
outFile = open('annotated_' + sys.argv[2], 'w')
lines = inFile.readlines()
inBuffer, lineCount = [], 1
index, while_list = 0, []
while index < len(lines):
	if lines[index].find("while") != -1:
		count_brace = 1
		while_line = index
		skip = False
		while lines[index].find("{") != -1: index += 1
		index += 1
		while count_brace:
			if lines[index].find("{") != -1:
				count_brace += 1
			if lines[index].find("}") != -1:
				count_brace -= 1
			if lines[index].find("assert") != -1:
				skip = True
			index += 1
		index -= 1
		if not skip:
			while_list.append(while_line + 1)
	index += 1

for line in lines:
	if ranges.has_key(lineCount) and lineCount in while_list:
		inBuffer.append(ranges[lineCount])
	inBuffer.append(line)
	lineCount += 1

outFile.write(''.join(inBuffer))
outFile.close()