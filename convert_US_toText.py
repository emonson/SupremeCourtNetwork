#!/usr/bin/env python

# Do date parsing and build initial copyright_test CouchDB database

import os, re, sys
from BeautifulSoup import BeautifulSoup, NavigableString, Tag
import string
from html2text import html2text
import vtk
import numpy as N
from vtk.util import numpy_support as VN

data_dir = '/Volumes/SciVis_LargeData/ArtMarkets/US'
out_dir = '/Volumes/SciVis_LargeData/ArtMarkets/US_txt'

os.makedirs(out_dir)

br = re.compile(r'<[bB][rR] *?/>')
bi = re.compile(r'<[bB]>')
bo = re.compile(r'</[bB]>')
ii = re.compile(r'<[iI]>')
io = re.compile(r'</[iI]>')

# Read in case table to grab caseid & usid
reader = vtk.vtkDelimitedTextReader()
reader.SetDetectNumericColumns(True)
reader.SetHaveHeaders(True)
reader.SetFileName('/Volumes/SciVis_LargeData/ArtMarkets/judicial/judicial.csv')
reader.GetFieldDelimiterCharacters()
reader.Update()

# VN doesn't support vtkStringArray -> Numpy
table = reader.GetOutput()
usid_vtk = table.GetColumnByName('usid')
case_refs = []
for c in range(usid_vtk.GetNumberOfValues()):
	case_refs.append(usid_vtk.GetValue(c))
usid = N.array(case_refs)

edges = vtk.vtkDelimitedTextReader()
edges.DetectNumericColumnsOn()
edges.SetFileName('/Volumes/SciVis_LargeData/ArtMarkets/judicial/allcites.txt')
edges.SetFieldDelimiterCharacters(' ')
edges.Update()

edges_table = edges.GetOutput()
start_node = VN.vtk_to_numpy(edges_table.GetColumn(0))
end_node = VN.vtk_to_numpy(edges_table.GetColumn(1))

# Get all nodes which appear in the citation network at any time
all_n = N.unique(N.concatenate((start_node, end_node)))

# IDs are 1-based and indices are 0-based
net_usids = usid[all_n-1]
print "Cases in net:", net_usids.shape[0]

count = 0
case_names = []

def count_files(arg, dirname, files):
	global count, case_names
	
	for file in files:
		fullpath = os.path.join(dirname, file)
		if os.path.isfile(fullpath) and (file != 'index.html'):
			
			# Reorganize file name to try to match usid
			pieces = file.split('.')
			file_id = "".join(pieces[:3])
			
			# Continue to next file if this id isn't in the network list
			if not (net_usids == file_id).sum():
				continue
			
			if (count % 100) == 0:
				print count
			count += 1

			case_names.append(file_id)
			
			f = open(fullpath,'r')
			s = f.read()
			f.close()
			
			# Replace all breaks, bolds and italics before doing soup
			s = br.sub(' ', s)
			s = bi.sub('', s)
			s = bo.sub('', s)
			s = ii.sub('', s)
			s = io.sub('', s)
			
			soup = BeautifulSoup(s)
			
			# Replace all footnote links with [-n-]
			aa = soup.findAll('a','footnote')
			for ll in aa:
				ll.replaceWith('[-' + ll.string + '-]')
			
			# Take out all paragraph numbering
			sp = soup.findAll('span','num')
			for ll in sp:
				ll.extract()
			
			# Take off footer
			ff = soup.find('div',{'id':'footer'})
			if ff is not None:
				ff.extract()
			
			# Convert HTML to contents string
			doc = html2text(str(soup))
			
			outpath = os.path.join(out_dir, file_id + ".txt")
			
			f = open(outpath, 'w')
			f.write(doc.encode('utf-8'))
			f.close()

os.path.walk(data_dir, count_files, None)

print "Total files processed:", count
case_names_array = N.array(case_names)
print "Cases not processed:"
print N.setdiff1d(net_usids, case_names_array)
