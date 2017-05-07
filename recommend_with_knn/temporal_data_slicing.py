# cut the data up into 12 slices of 1 month each, and tell us what the results
# are for each slice

import recommend_with_knn as steam_rec

last_collection_time = 1494012977000

# month -> ms = days * hours * minutes * seconds * ms
month_ms = 1 * 30 * 24 * 60 * 60 * 1000

curators = steam_rec.get_data('../recommend_by_types/curators.json')
games = steam_rec.get_data('../recommend_by_types/games.json')

k = 20  # TODO: smarter

our_game = {
    'Open World': 0.2,
    'RPG': 0.2,
    'Adventure': 0.2,
    'Fantasy': 0.2,
    'Singleplayer': 0.1,
    'Atmospheric': 0.1,
    'Character Customization': 0.1
}

for i in range(12):
    end_time = last_collection_time - month_ms * i

    graph = steam_rec.build_graph(
        curators, games, end_time - month_ms, end_time
    )

    recommended_curator_id = steam_rec.predict(
        graph, our_game, k
    )

    curator_name = curators[recommended_curator_id]['name']

    print('The recommended curator {0} for time slice {1}'.format(
        curator_name, i)
    )
