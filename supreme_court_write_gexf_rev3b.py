# This version uses Fast2D and only shows the largest connected component

import vtk
import numpy as N
from vtk.util import numpy_support as VN
import time
import networkx as nx

reader = vtk.vtkDelimitedTextReader()
reader.SetDetectNumericColumns(True)
reader.SetHaveHeaders(True)
reader.SetFileName('/Volumes/SciVis_LargeData/ArtMarkets/judicial/judicial.csv')
reader.GetFieldDelimiterCharacters()
reader.Update()

table = reader.GetOutput()
year = VN.vtk_to_numpy(table.GetColumnByName('year'))
caseid = VN.vtk_to_numpy(table.GetColumnByName('caseid'))

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
cite_year = year[start_node - 1]

lrg = vtk.vtkBoostExtractLargestComponent()

# years_list = [1820,1825,1830,1835]
years_list = [1880, 1900, 1920, 1940, 1960, 1980]

# for yr in range(1820,2000):
for yr in years_list:

	print 'Year: ' + str(yr)
	
	# Shift over previous results to prev variables
	if yr != years_list[0]:
		prevPoints = vtk.vtkFloatArray()
		prevPoints.DeepCopy(lrg.GetOutput().GetPoints().GetData())
		# print VN.vtk_to_numpy(prevPoints)
		prevIDs = vtk.vtkIntArray()
		prevIDs.DeepCopy(lrg.GetOutput().GetVertexData().GetArray('case_id'))
		# Create dictionary for point coordinate lookup
		point_pos = {}
		for ii in range(prevIDs.GetNumberOfTuples()):
			point_pos[prevIDs.GetTuple1(ii)] = prevPoints.GetTuple3(ii)

	# Break pipeline while set up new graph
	# if yr != years_list[0]:
		# lrg.RemoveAllInputs()
		# del table, col0, col1, val, rawGraph, tgraph, currCoords, constraintArray, constraintData, yearData, vertexData
	
	# Build table of edges for correct year range
	start_n = start_node[cite_year < yr]
	end_n = end_node[cite_year < yr]
	all_n = N.unique(N.concatenate((start_n,end_n)))
	
	table = vtk.vtkTable()
	col0 = VN.numpy_to_vtk(start_n, deep=True)
	col0.SetName('start_node')
	col1 = VN.numpy_to_vtk(end_n, deep=True)
	col1.SetName('end_node')
	val = VN.numpy_to_vtk( N.ones(cite_year[cite_year < yr].shape) )
	val.SetName('weight')
	
	table.AddColumn(col0)
	table.AddColumn(col1)
	table.AddColumn(val)
	
	# Only use cases as nodes if they've cited others
	node_table = vtk.vtkTable()
	col2 = VN.numpy_to_vtk(all_n, deep=True)
	col2.SetName('case_id')
	col3 = VN.numpy_to_vtk(year[all_n-1], deep=True)
	col3.SetName('year')
	node_table.AddColumn(col2)
	node_table.AddColumn(col3)
	
	# Display all cases, even if they don't have any citations...?
# 	node_table = vtk.vtkTable()
# 	col2 = VN.numpy_to_vtk(caseid[year < yr], deep=True)
# 	col2.SetName('case_id')
# 	col3 = VN.numpy_to_vtk(year[year < yr], deep=True)
# 	col3.SetName('year')
# 	node_table.AddColumn(col2)
# 	node_table.AddColumn(col3)
	
	# print '\tConverting table to graph'
	tgraph = vtk.vtkTableToGraph()
	tgraph.SetDirected(False)
	tgraph.SetInput(table)
	tgraph.AddLinkVertex('start_node', 'case_id', False)
	tgraph.AddLinkVertex('end_node', 'case_id', False)
	tgraph.AddLinkEdge('start_node', 'end_node')
	tgraph.SetVertexTableConnection(node_table.GetProducerPort())
	tgraph.Update()
	
	rawGraph = vtk.vtkUndirectedGraph()
	rawGraph.DeepCopy(tgraph.GetOutput())
	print rawGraph.GetVertexData()
	print rawGraph.GetEdgeData()

	# Put in positions for already layed-out vertices
	# print '\tAssigning previous coordinates and constraints'
	if yr != years_list[0]:
		currPoints = rawGraph.GetPoints().GetData()
		currIDs = rawGraph.GetVertexData().GetArray('case_id')
		
		for ii in range(currPoints.GetNumberOfTuples()):
			id = currIDs.GetTuple1(ii)
			if id in point_pos:
				pp = point_pos[id]
				currPoints.SetTuple3(ii, pp[0], pp[1], pp[2])
			else:
				pp = 2*N.random.randn(3)
				currPoints.SetTuple3(ii, pp[0], pp[1], pp[2])
		
		# print VN.vtk_to_numpy(currPoints)
	
	else:
		currPoints = rawGraph.GetPoints().GetData()
		
		for ii in range(currPoints.GetNumberOfTuples()):
			pp = 10*N.random.randn(3)
			currPoints.SetTuple3(ii, pp[0], pp[1], pp[2])
		
		# print VN.vtk_to_numpy(currPoints)
		
	# print lrg.GetOutput()
	lrg.SetInputConnection(rawGraph.GetProducerPort())
	lrg.Update()
	
	out_graph = lrg.GetOutput()
	it = vtk.vtkEdgeListIterator()
	out_graph.GetEdges(it)
	edge_list = []
	
	for ii in range(out_graph.GetNumberOfEdges()):
		ed = it.NextGraphEdge()
		edge_list.append((ed.GetSource(), ed.GetTarget()))
	
	H = nx.Graph(edge_list)
	nx.write_gexf(H, 'us_' + str(yr) + '.gexf')
# 	H = nx.DiGraph(edge_list)
# 	nx.write_gexf(H, 'us_di_' + str(yr) + '.gexf')

