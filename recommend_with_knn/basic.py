# Basic
# basic example of how SteamRec works

import operator
import recommend_with_knn as steam_rec

curators = steam_rec.get_data('curators.json')
games = steam_rec.get_data('games.json')

# see paper for why we chose these numbers
k = 50
n = 10

our_game = {
    'Open World': 0.2,
    'RPG': 0.2,
    'Adventure': 0.2,
    'Fantasy': 0.15,
    'Singleplayer': 0.15,
    'Atmospheric': 0.1,
    'Character Customization': 0.1
}

graph = steam_rec.build_graph(curators, games)

curator_ids = steam_rec.predict(
    graph, our_game, k, n
)

s = 'Basic prediction with k: {} and n: {}, we\'ve been recommended:'
print(s.format(k, n))


for curator_id in curator_ids:
    print('  ' + curators[curator_id]['name'])
