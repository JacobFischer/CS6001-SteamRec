# recommends games to curators using a knn method
# each item in the graph is a game, with a list of curators recommending that game, weighted by time of recommendation
# distance between games is calculated as the euclidean distance between the games' normalized tag ratios
# the predicted curator for each game is the largest weighted curator among k neighbors

import json
import math

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

def build_graph(curators_path, games_path):
	# builds and returns a graph of games, their tag ratios, and curators with time weights
	# this takes about 3 minutes on my laptop
	with open(curators_path, 'r') as file:
		curators = json.load(file)

	with open(games_path, 'r') as file:
		games = json.load(file)

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
			# get the time bias for this recommendation, calculated as the period between the launch of steam curators (roughly sept 22 2014) and the time of recommendation,
			# divided by the period between now and the launch of steam curators
			# this evaluates to near 1 for very recent recommendations and near 0 for very old recommendations
			# note: the epochs here (and in the json data) are in milliseconds
			recommendationBias = max(((recommendationInfo['epoch']) - 1411344000000) / (1494012977000 - 1411344000000), 0)

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
	# load the list of curators so we can get the name from the id
	with open(curatorPath, 'r') as file:
		curators = json.load(file)

	# build the graph
	print('Building graph')
	graph = build_graph(curatorPath, gamesPath)
	
	# set up an example game to recommend
	exampleGameTagRatios = dict()
	exampleGameTagRatios['Open World'] = 0.2
	exampleGameTagRatios['RPG'] = 0.2
	exampleGameTagRatios['Adventure'] = 0.2
	exampleGameTagRatios['Fantasy'] = 0.2
	exampleGameTagRatios['Singlepalyer'] = 0.1
	exampleGameTagRatios['Atmospheric'] = 0.1
	exampleGameTagRatios['Character Customization'] = 0.1

	# try with different values for k
	for kTest in [1,2,3,5,10,20,50]:
		print('Testing k value of {0}'.format(str(kTest)))
		recommendedCuratorID = predict(graph, exampleGameTagRatios, kTest)
		print('The recommended curator ID is {0}'.format(str(recommendedCuratorID)))
		recommendedCuratorName = curators[recommendedCuratorID]['name']
		print('The name of this curator is {0}'.format(recommendedCuratorName))
