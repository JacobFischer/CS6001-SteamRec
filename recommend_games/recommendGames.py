import json

# surprise utilities
from surprise import Dataset, Reader, print_perf, evaluate
# surprise algorithms
from surprise import SVD, NMF, KNNBasic

def loadData(path, outputPath):
	### reads the json data at 'path' and generates a curator - item - rating data matrix file for surprise to use
	### fair warning: this generates like a 140MB file and takes a minute or so
	# load the data
	with open(path) as file:
		jsonData = json.load(file)

	# get all the items recommended by at least one curator
	allItems = set()
	for itemList in jsonData.values():
		allItems = allItems.union(set(itemList))

	# get the list of curators
	curators = jsonData.keys()

	# build the data matrix as a list of tuples of (curator, item, rating)
	dataMatrix = []
	for c in curators:
		for i in allItems:
			if i in jsonData[c]:
				recommended = '1'
			else:
				recommended = '0'
			dataMatrix.append( (c, i, recommended) )

	# write the data to a file because surprise needs to read from a file
	with open(outputPath, 'w') as dataMatrixFile:
		for d in dataMatrix:
			line = '\t'.join(d) + '\n'
			dataMatrixFile.write(line)

def buildDataset(path):
	# build a dataset for surprise using the data matrix at the file at 'path'
	reader = Reader(line_format='user item rating', sep='\t')
	data = Dataset.load_from_file(path, reader=reader)
	data = data.build_full_trainset() # we will not be splitting for cross-validation; we are training on all this data
	return data

if __name__ == '__main__':
	# this whole process takes ~15-20 minutes on my laptop
	# define data file locations
	rawData = '../get_curators_apps/curator_to_appids.json' # where we find the json with the curator data
	dataMatrixPath = 'dataMatrix.txt'   # where we will write the data matrix to when we create it

	# get data
	print('Getting data matrix')
	loadData(rawData, dataMatrixPath)   # you can skip this if dataMatrix.txt already exists
	data = buildDataset(dataMatrixPath)

	# train recommender
	print('Training recommender')
	algo = SVD()    # we can substitute another learning algorithm here
	algo.train(data)
