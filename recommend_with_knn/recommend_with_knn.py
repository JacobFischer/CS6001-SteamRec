# recommends games to curators using a knn method
# each item in the graph is a game, with a list of curators recommending that game, weighted by time of recommendation
# distance between games is calculated as the euclidean distance between the games' normalized tag ratios
# the predicted curator for each game is the largest weighted curator among k neighbors

import json
import math
import os.path

def euclidean_dist(tagRatios1, tagRatios2):
	# compute the euclidean distance between two dictionaries of tag ratios
	# get all the tags that appear in either dict
	allTags = set(list(tagRatios1.keys()) + list(tagRatios2.keys()))
	# compute the sum under the square root
	s = 0
	for t in allTags:
		x = tagRatios1.get(t, 0)
		y = tagRatios2.get(t, 0)
		s += (x-y)**2
	# sqrt and return
	return math.sqrt(s)

def get_data(path):
	with open(path, 'r') as file:
		return json.load(file)

def build_graph(curators, games, startTime=1411344000000, endTime=1494012977000, cache=True):
	"""
	Builds the graph used in kNN, this is a slow process and will probably take a few minutes A percentage should print as it executes

	Args:
		curators - the dict of all curators and their recommendations
		games - the dict of all games (appid) and their metadata such as tags
		[startTime] - the minimum time to consider, defaults to a date roughly that of the time Steam Curators launched (roughly sept 22 2014)
		[endTime] - the maximum time to consider, defaults to may 5th, the last time the dataset was recollected (as otherwise we'd penalize games for not being recent if we used the current system time)

	Returns:
		the graph built for kNN clustering
	"""

	# check if we cached this graph
	if cache:
		cached_filename = './cached-{}-{}.json'.format(startTime, endTime)
		if os.path.isfile(cached_filename):
			print("loading graph from cached file " + cached_filename)
			# load it from the cache
			return get_data(cached_filename)

	graph = dict()

	# put each game in the graph
	numGames = len(games)
	gameCount = 0
	for gameID, gameData in games.items():
		print(("%.2f" % (100 * gameCount / numGames)) + '% done', end='\r')
		gameCount += 1

		graphGame = dict()

		# get the list of IDs of curators that recommend this game and their time-bias
		recommendations = []
		for curatorID, curatorData in curators.items():
			recommendationInfo = next((g for g in curatorData['list'] if g['appid'] == gameID), None)
			if not recommendationInfo:
				# this curator does not recommend this game, so skip him
				continue
			if recommendationInfo['info']:
				# this is an info review, skip this curator
				continue

			recommendationEpoch = recommendationInfo['epoch']
			if recommendationEpoch > endTime or recommendationEpoch < startTime:
				# then the recommendation is out of the range we are considering, so skip it
				continue

			# get the time bias for this recommendation, calculated as the period between the launch of steam curators (roughly sept 22 2014) and the time of recommendation,
			# divided by the period between now and the launch of steam curators
			# this evaluates to near 1 for very recent recommendations and near 0 for very old recommendations
			# note: the epochs here (and in the json data) are in milliseconds
			recommendationBias = max(((recommendationEpoch) - startTime) / (endTime - startTime), 0)

			# make the bias negative if the recommendation is negative
			if not recommendationInfo['recommended']:
				recommendationBias *= -1

			# add this curator-recommendation pair to the list of recommendation
			recommendations.append((curatorID, recommendationBias))

		# add the list of recommendations to this game
		graphGame['recommendations'] = recommendations

		# if this game has no tags, skip it
		if 'tags' not in gameData or not gameData['tags']:
			continue

		# calculate the tag ratios for this game
		totalTags = sum(gameData['tags'].values())
		tagRatios = dict()
		for tag, numTagged in gameData['tags'].items():
			tagRatios[tag] = numTagged / totalTags

		# add the tag ratios to this game
		graphGame['tagRatios'] = tagRatios

		# add this game to the graph
		graph[gameID] = graphGame

	print('\nDone!')  # \n to clear the \r in above loop

	# if we are cacheing, cache it
	if cache:
		with open(cached_filename, 'w') as file:
			json.dump(graph, file)

	return graph

def predict(graph, tag_ratios, k):
	# return a predicted curator by looking at the k nearest neighbors of a game given a dictionary of its tag ratios
	# get the games in the graph
	neighbors = graph.values()
	# sort the game list by distance to this list
	nearestNeighbors = sorted(neighbors, key=lambda g: euclidean_dist(tag_ratios, g['tagRatios']))
	# get the k nearest neighbors
	kNearestNeighbors = nearestNeighbors[:k]
	# look at each curator that recommends each of the games and measure their bias towards this game
	totalRecommendations = dict()
	for g in kNearestNeighbors:
		for curatorID, recommendationBias in g['recommendations']:
			if curatorID not in totalRecommendations.keys():
				totalRecommendations[curatorID] = 0
			totalRecommendations[curatorID] += recommendationBias
	# get the curatorID with the maximum total recommendation
	recommendedCuratorID = max(totalRecommendations, key=totalRecommendations.get)

	return recommendedCuratorID

if __name__ == '__main__':
	curatorPath = '../recommend_by_types/curators.json'
	gamesPath = '../recommend_by_types/games.json'

	curators = get_data(curatorPath)
	games = get_data(gamesPath)

	# build the graph
	print('Building graph')

	graph = build_graph(curators, games)
	
	# set up an example game to recommend
	exampleGameTagRatios = {
		'Open World': 0.2,
		'RPG': 0.2,
		'Adventure': 0.2,
		'Fantasy': 0.2,
		'Singleplayer': 0.1,
		'Atmospheric': 0.1,
		'Character Customization': 0.1
	}

	# try with different values for k
	for kTest in [1,2,3,5,10,20,50]:
		print('Testing k value of {0}'.format(str(kTest)))
		recommendedCuratorID = predict(graph, exampleGameTagRatios, kTest)
		print('The recommended curator ID is {0}'.format(str(recommendedCuratorID)))
		recommendedCuratorName = curators[recommendedCuratorID]['name']
		print('The name of this curator is {0}'.format(recommendedCuratorName))
