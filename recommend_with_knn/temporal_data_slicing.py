# Temporal Data Slicing
# cut the data up into 12 slices of 1 month each, and tell us what the results
# are for each slice

import operator
import recommend_with_knn as steam_rec

# may 5th
last_collection_time = 1494012977000

# month -> ms = days * hours * minutes * seconds * ms
month_ms = 1 * 30 * 24 * 60 * 60 * 1000

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

counts = {}

# change these to control the time slices
month_span = 4  # 4 months for a quarter, 1 for month
num_spans = 4

for i in range(num_spans):
    end_time = last_collection_time - month_ms * i * month_span

    graph = steam_rec.build_graph(
        curators,
        games,
        startTime=end_time - int(month_ms * month_span),
        endTime=end_time
    )

    curator_ids = steam_rec.predict(
        graph, our_game, k, n
    )

    s = 'Data slice {} with k: {} and n: {}, we\'ve been recommended:'
    print(s.format(i, k, n))

    for curator_id in curator_ids:
        curator_name = curators[curator_id]['name']

        print('  ' + curator_name)

        if curator_name not in counts:
            counts[curator_name] = 1
        else:
            counts[curator_name] += 1

# now let's say who was recommend the most
sorted_counts = sorted(
    counts.items(),
    key=operator.itemgetter(1),
    reverse=True
)

for t in sorted_counts:
    print('{}, {}'.format(t[0], t[1]))
