# Writing out whole dynamic graph in gexf format
# where both the start node and edge have a "start date".
# This one doesn't just do the largest connected component.

import vtk
import numpy as N
from vtk.util import numpy_support as VN
import time
import networkx as nx

print 'Reading source files'

reader = vtk.vtkDelimitedTextReader()
reader.SetDetectNumericColumns(True)
reader.SetHaveHeaders(True)
reader.SetFileName('/Volumes/SciVis_LargeData/ArtMarkets/judicial/judicial.csv')
reader.GetFieldDelimiterCharacters()
reader.Update()

table = reader.GetOutput()
year = VN.vtk_to_numpy(table.GetColumnByName('year'))
caseid = VN.vtk_to_numpy(table.GetColumnByName('caseid'))
usid_vtk = table.GetColumnByName('usid')

edges = vtk.vtkDelimitedTextReader()
edges.DetectNumericColumnsOn()
edges.SetFileName('/Volumes/SciVis_LargeData/ArtMarkets/judicial/allcites.txt')
edges.SetFieldDelimiterCharacters(' ')
edges.Update()

edges_table = edges.GetOutput()
start_node = VN.vtk_to_numpy(edges_table.GetColumn(0))
end_node = VN.vtk_to_numpy(edges_table.GetColumn(1))

# This array is the same length as the number of edges
# and denotes the year in which the start node was decided
start_year = year[start_node - 1]
end_year = year[end_node - 1]

print 'Building graph'

# Building graph with networkx for convenience, but
# eventually writing GEXF format manually since 'start'
# XML attribute not written properly with write_gexf
G = nx.Graph()

for ii in range(start_node.size):

	if (ii%10000 == 0):
		print '  ', ii
	
	G.add_node(start_node[ii])
	G.node[start_node[ii]]['label'] = usid_vtk.GetValue(start_node[ii]-1)
	G.node[start_node[ii]]['start'] = int(start_year[ii])
	G.add_node(end_node[ii])
	G.node[end_node[ii]]['label'] = usid_vtk.GetValue(end_node[ii]-1)
	G.node[end_node[ii]]['start'] = int(end_year[ii])
	G.add_edge(start_node[ii], end_node[ii])
	G.edge[start_node[ii]][end_node[ii]]['start'] = int(start_year[ii])

nodes = [n for n in G.nodes_iter(data=True)]
edges = [e for e in G.edges_iter(data=True)]

print 'Writing file'

# Write file
f = open('us_allDyn.gexf', 'w')

# Header
aa = '<?xml version="1.0" encoding="UTF-8"?>\n\
<gexf xmlns="http://www.gexf.net/1.2draft" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd" version="1.2">\n\
    <graph mode="dynamic" defaultedgetype="undirected" timeformat="date">\n'
f.write(aa)

print '  Nodes'

# Nodes
f.write('        <nodes>\n')
for (id, d) in nodes:
	f.write('            <node id="%d" label="%s" start="%d-01-01" />\n' % (id, d['label'], d['start']))
f.write('        </nodes>\n')

print '  Edges'

# Edges
f.write('        <edges>\n')
id = 0
for (src, tgt, d) in edges:
	f.write('            <edge id="%d" source="%d" target="%d" start="%d-01-01" />\n' % (id, src, tgt, d['start']))
	id += 1
f.write('        </edges>\n')

# Footer
aa = '    </graph>\n\
</gexf>'
f.write(aa)
f.close()


