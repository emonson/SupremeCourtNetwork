import vtk
import numpy as N
from vtk.util import numpy_support as VN
import time

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

view = vtk.vtkGraphLayoutView()
# Apply a theme to the views
theme = vtk.vtkViewTheme.CreateMellowTheme()
# theme = vtk.vtkViewTheme.CreateOceanTheme()
theme.SetLineWidth(2)
theme.SetPointSize(6)
theme.SetCellColor(0.8, 0.8, 0.8)
theme.SetSelectedCellColor(1,1,1)
theme.SetSelectedPointColor(1,1,1)
theme.SetOutlineColor(0.6,0.6,0.6)
# theme.SetPointOpacity(0.5)
theme.SetPointHueRange(1.0,1.0)
theme.SetPointSaturationRange(1.0,1.0)
theme.SetPointValueRange(0.0,1.0)
theme.SetPointAlphaRange(0.2,0.8)

theme.SetScalePointLookupTable(True)

nl = theme.GetPointLookupTable().GetNumberOfTableValues()
theme.GetPointLookupTable().Build()
theme.GetPointLookupTable().SetTableValue(nl-1, [0.0, 0.33, 0.66, 1.0])

view.SetLayoutStrategyToPassThrough()
view.SetVertexColorArrayName("year")
view.SetColorVertices(True)        
view.SetEdgeVisibility(True)
view.ApplyViewTheme(theme)

strategy = vtk.vtkForceDirectedLayoutStrategy()
strategy.RandomInitialPointsOff()
strategy.SetIterationsPerLayout(2)
# strategy.SetGraphBounds(-10,10,-10,10,0,0)
layout = vtk.vtkGraphLayout()
layout.SetLayoutStrategy(strategy)

view.GetRenderWindow().SetSize(600,600)
view.ResetCamera()
view.Render()

years_list = [1820,1825,1830,1835]

for yr in range(1820,1900):
	
	print 'Year: ' + str(yr)
	
	strategy.SetMaxNumberOfIterations(500)
	strategy.SetInitialTemperature(0.02)
	# Want to show initial new connections without moving the points much
	strategy.SetIterationsPerLayout(1)

	# Shift over previous results to prev variables
	if yr != years_list[0]:
		prevPoints = vtk.vtkFloatArray()
		prevPoints.DeepCopy(layout.GetOutput().GetPoints().GetData())
		# print VN.vtk_to_numpy(prevPoints)
		prevIDs = vtk.vtkIntArray()
		prevIDs.DeepCopy(layout.GetOutput().GetVertexData().GetArray('case_id'))
		# Create dictionary for point coordinate lookup
		point_pos = {}
		for ii in range(prevIDs.GetNumberOfTuples()):
			point_pos[prevIDs.GetTuple1(ii)] = prevPoints.GetTuple3(ii)

	# Break pipeline while set up new graph
	if yr != years_list[0]:
		layout.RemoveAllInputs()
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
	tgraph.SetDirected(True)
	tgraph.SetInput(table)
	tgraph.AddLinkVertex('start_node', 'case_id', False)
	tgraph.AddLinkVertex('end_node', 'case_id', False)
	tgraph.AddLinkEdge('start_node', 'end_node')
	tgraph.SetVertexTableConnection(node_table.GetProducerPort())
	tgraph.Update()
	
	rawGraph = vtk.vtkDirectedGraph()
	rawGraph.DeepCopy(tgraph.GetOutput())

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
				pp = 0.1*N.random.randn(3)
				currPoints.SetTuple3(ii, pp[0], pp[1], pp[2])
		
		# print VN.vtk_to_numpy(currPoints)
	
	else:
		currPoints = rawGraph.GetPoints().GetData()
		
		for ii in range(currPoints.GetNumberOfTuples()):
			pp = 10*N.random.randn(3)
			currPoints.SetTuple3(ii, pp[0], pp[1], pp[2])
		
		# print VN.vtk_to_numpy(currPoints)
		
	layout.SetInputConnection(rawGraph.GetProducerPort())

	# view.RemoveAllRepresentations()
	if yr == years_list[0]:
		view.AddRepresentationFromInputConnection(layout.GetOutputPort())
	
	# print '\tInitial reset and render'
	view.ResetCamera()
	view.Render()
	time.sleep(1.0)
	strategy.SetIterationsPerLayout(50)
	
	while not strategy.IsLayoutComplete():
		# time.sleep(0.1)
		layout.Modified()
		view.ResetCamera()
		view.Render()
	
	# Give it another jolt for a better layout
	strategy.SetMaxNumberOfIterations(1000)
	strategy.SetInitialTemperature(1.0)
	strategy.Initialize()
	while not strategy.IsLayoutComplete():
		# time.sleep(0.1)
		layout.Modified()
		view.ResetCamera()
		view.Render()
		
view.GetInteractor().Start()
