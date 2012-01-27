import vtk
import numpy as N
from vtk.util import numpy_support as VN
import time

currGraph = vtk.vtkDirectedGraph()
prevGraph = vtk.vtkDirectedGraph()

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

# view.ApplyViewTheme(theme)

# strategy = vtk.vtkSimple2DLayoutStrategy()
strategy = vtk.vtkConstrained2DLayoutStrategy()
strategy.SetInputArrayName('constraint')
strategy.SetMaxNumberOfIterations(2000)
strategy.SetInitialTemperature(5.0)
strategy.SetCoolDownRate(200.0)
strategy.SetIterationsPerLayout(50)
layout = vtk.vtkGraphLayout()
layout.SetLayoutStrategy(strategy)

view.GetRenderWindow().SetSize(600,600)
view.ResetCamera()
view.Render()

years_list = [1820,1825,1830,1835]

for yr in range(1820,1850):
	
	print 'Year: ' + str(yr)
	
	# Shift over previous results to prev variables
	if yr != years_list[0]:
		prevCoords = VN.vtk_to_numpy(currGraph.GetPoints().GetData()).copy()
	else:
		prevCoords = N.zeros((cite_year[cite_year < yr].shape[0],3))
	# prevGraph.DeepCopy(currGraph)
	
	# Break pipeline while set up new graph
	if yr != years_list[0]:
		layout.RemoveAllInputs()
		# del table, col0, col1, val, rawGraph, tgraph, currCoords, constraintArray, constraintData, yearData, vertexData
	
	# Build table of edges for correct year range
	table = vtk.vtkTable()
	col0 = VN.numpy_to_vtk(start_node[cite_year < yr], deep=True)
	col0.SetName('start_node')
	col1 = VN.numpy_to_vtk(end_node[cite_year < yr], deep=True)
	col1.SetName('end_node')
	val = VN.numpy_to_vtk( N.ones(cite_year[cite_year < yr].shape) )
	val.SetName('weight')
	
	table.AddColumn(col0)
	table.AddColumn(col1)
	table.AddColumn(val)
	
	print '\tConverting table to graph'
	tgraph = vtk.vtkTableToGraph()
	tgraph.SetDirected(True)
	tgraph.SetInput(table)
	tgraph.AddLinkVertex('start_node', 'stuff', False)
	tgraph.AddLinkVertex('end_node', 'stuff', False)
	tgraph.AddLinkEdge('start_node', 'end_node')
	tgraph.Update()
	
	rawGraph = vtk.vtkDirectedGraph()
	rawGraph.DeepCopy(tgraph.GetOutput())
	rawGraph = tgraph.GetOutput()
	rawGraph.Update()
	
	# Will assign non-zero constraint for any old nodes
	constraintArray = N.zeros(rawGraph.GetNumberOfVertices())
	
	for ii in range(prevCoords.shape[0]):
		if yr != years_list[0]:
			constraintArray[ii] = 0.95
		else:
			constraintArray[ii] = 0.0

	# Set 'constraint' vertex data from numpy array
	constraintData = VN.numpy_to_vtk(constraintArray, deep=True)
	constraintData.SetName('constraint')
	yearData = VN.numpy_to_vtk(cite_year[cite_year < yr], deep=True)
	yearData.SetName('year')
	vertexData = rawGraph.GetVertexData()
	vertexData.AddArray(constraintData)
	vertexData.AddArray(yearData)
	rawGraph.Modified()
	
	# print VN.vtk_to_numpy(rawGraph.GetVertexData().GetArray('constraint'))
	# print N.array2string(VN.vtk_to_numpy(rawGraph.GetPoints().GetData()), precision=3, suppress_small=1)
	
	# NOTE: Changing input is screwing up all of my efforts to set the point coordinates...
	print '\tChanging inputs'
	# layout.RemoveAllInputs()
	layout.SetInput(rawGraph)
	# layout.Modified()
	# strategy.Initialize()
	# layout.Update()
	view.Render()

	# Put in positions for already layed-out vertices
	print '\tAssigning previous coordinates and constraints'
	# Accessing values directly
	currCoords = VN.vtk_to_numpy(rawGraph.GetPoints().GetData())
	print currCoords
	# Jitter points
	# currCoords[:,:] = N.random.randn(currCoords.shape[0], currCoords.shape[1])
	
	for ii in range(prevCoords.shape[0]):
		currCoords[ii,:] = prevCoords[ii,:]
	
# 	print N.mean(prevCoords,0)
	print currCoords
	
	
	# view.RemoveAllRepresentations()
	if yr == years_list[0]:
		view.SetLayoutStrategyToPassThrough()
		view.AddRepresentationFromInputConnection(layout.GetOutputPort())
	
	view.SetVertexColorArrayName("year")
	view.SetColorVertices(True)        
	view.SetEdgeVisibility(True)
	view.ApplyViewTheme(theme)
	
	print '\tInitial reset and render'
	view.ResetCamera()
	view.Render()
	
	count = 0
	while not strategy.IsLayoutComplete():
		# time.sleep(0.2)
		# print "iter"
		layout.Modified()
		view.ResetCamera()
		view.Render()
		if count == 0:
			print currCoords
		count += 1
		# print VN.vtk_to_numpy(layout.GetOutput().GetVertexData().GetArray('year'))
			
	# Copy over graph after layout and disconnect from all setup steps
	print '\tCopying over resulting graph'
	del currGraph
	currGraph = vtk.vtkDirectedGraph()
	currGraph.DeepCopy(layout.GetOutputDataObject(0))
	# print N.array2string(VN.vtk_to_numpy(currGraph.GetPoints().GetData()), precision=3, suppress_small=1)
	
	
	
# for ii in range(10):
#     # strategy.Initialize()
#     layout.Modified()
#     print 'Modified'
#     view.Update()

view.GetInteractor().Start()
