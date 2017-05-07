# recommends games to curators using a knn method
# each item in the graph is a game, with a list of curators recommending that game, weighted by time of recommendation
# distance between games is calculated as the euclidean distance between the games' normalized tag ratios
# the predicted curator for each game is the largest weighted curator among k neighbors

import json
import math
import random

import os.path

def sampleRecentRecommendations(curators, games, n, cutoffEpoch):
	# returns a list of n game ids for games recently recommended by a curator
	allRecommendations = []
	for cData in curators.values():
		for g in cData['list']:
			if g['recommended'] and not g['info'] and g['epoch'] >= cutoffEpoch and g['appid'] in games.keys():
				allRecommendations.append(g['appid'])
	return random.sample(allRecommendations, n)



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

def build_graph(curators, games, excludedGames=None, startTime=1411344000000, endTime=1494012977000, cache=True):
	"""
	Builds the graph used in kNN, this is a slow process and will probably take a few minutes A percentage should print as it executes
	If exludedGames is not None, then every game ID in excludedGames will be excluded from the graph

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
	if excludedGames is not None:
		numGames -= len(excludedGames)
	gameCount = 0
	for gameID, gameData in games.items():
		# skip this game if we are excluding it
		if excludedGames is not None and gameID in excludedGames:
			continue

		# print progress
		print(("%.2f" % (100 * gameCount / numGames)) + '% done', end='\r')
		gameCount += 1

		# set up dictionary for game
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

		# if nobody recommends this game, don't put it in the graph
		if len(recommendations) == 0:
			continue

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

def predict(graph, tag_ratios, k, n):
	# return n predicted curators by looking at the k nearest neighbors of a game given a dictionary of its tag ratios
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
	# sort the curators by max recommendation weight
	allRecommendingCurators = list(totalRecommendations.keys())
	allRecommendingCurators.sort(key=lambda c: totalRecommendations[c], reverse=True)

	# get the top n curators
	recommendedCuratorIDs = allRecommendingCurators[:n]

	return recommendedCuratorIDs

if __name__ == '__main__':
	curatorPath = '../recommend_by_types/curators.json'
	gamesPath = '../recommend_by_types/games.json'

	curators = get_data(curatorPath)
	games = get_data(gamesPath)

	excludedGames = sampleRecentRecommendations(curators, games, 100, 1488399304000)

	# build the graph
	print('Building graph')

	graph = build_graph(curators, games, excludedGames=excludedGames)


	# try to recommend the excluded games
	scores = dict()
	for test_gID in excludedGames:

		# get the tag ratios for this game
		gData = games[test_gID]
		testGameTagRatios = dict()
		# skip this game if it has no tags
		if 'tags' not in gData or not gData['tags']:
			continue
		totalTags = sum(gData['tags'].values())
		for tag, numTagged in gData['tags'].items():
			testGameTagRatios[tag] = numTagged / totalTags

		print('Testing game with ID {0} and name {1}'.format(str(test_gID), gData['name']))

		# try with different values for k
		for kTest in [1,2,3,5,10,20,50]:
			for nTest in [1,2,3,5,10]:
				if (kTest, nTest) not in scores.keys():
					scores[(kTest, nTest)] = 0
				print('Testing k value of {0} and n value of {1}'.format(str(kTest), str(nTest)))
				recommendedCuratorIDs = predict(graph, testGameTagRatios, kTest, nTest)
				print('The recommended curators are:')
				for recommendedCuratorID in recommendedCuratorIDs:
					print('{0}, with name {1}'.format(recommendedCuratorID, curators[recommendedCuratorID]['name']))

				# see if we predicted correctly by getting all the games recommended by these curators
				allRecommendedGames = []
				for recommendedCuratorID in recommendedCuratorIDs:
					allRecommendedGames += list(g['appid'] for g in curators[recommendedCuratorID]['list'])
				if test_gID in allRecommendedGames:
					print('At least one of these curators recommends this game')
					scores[(kTest, nTest)] += 1
				else:
					print('None of these curators recommends this game')


	print(scores)