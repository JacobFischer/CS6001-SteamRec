import json

# surprise utilities
from surprise import Dataset, Reader, print_perf, evaluate
# surprise algorithms
from surprise import SVD, NMF, KNNBasic
# testing
from surprise import evaluate, print_perf


def build_matrix(curators_path, games_path):
    with open(curators_path, 'r') as file:
        curators = json.load(file)

    with open(games_path, 'r') as file:
        games = json.load(file)

    matrix = {}

    for curator_id, curator_data in curators.items():
        our_tags = {}  # will be dict of tag to count
        matrix[curator_id] = our_tags

        for recommendation_data in curator_data['list']:
            if recommendation_data['info']:
                # then it was some info post, so skip it
                continue

            # if the recommended the game
            scalar = 1 if recommendation_data['recommended'] else -1
            appid = recommendation_data['appid']
            if appid not in games:
                # we don't have data on that game
                # (they probably opted out of being in the API)
                # so skip it
                continue

            game = games[appid]

            if 'tags' not in game or not game['tags']:
                # game is so unknown, no one tagged it, so it has no valid data
                continue

            for tag, count in game['tags'].items():
                if tag not in our_tags:
                    our_tags[tag] = 0

                our_tags[tag] += scalar * count

    return matrix


def matrix_to_dataset(matrix):
    output_path = 'temp.txt'

    # write the data to a file because surprise needs to read from a file
    with open(output_path, 'w') as file:
        for curator_id, curator_tags in matrix.items():
            for tag, count in curator_tags.items():
                file.write('\t'.join([curator_id, tag, str(count)]) + '\n')

    reader = Reader(line_format='user item rating', sep='\t')
    dataset = Dataset.load_from_file(output_path, reader=reader)
    return dataset.build_full_trainset()   # we will not be splitting


if __name__ == '__main__':
    print('creating matrix')
    matrix = build_matrix('curators.json', 'games.json')

    print('converting to dataset')
    dataset = matrix_to_dataset(matrix)

    algo = SVD()  # we can substitute another learning algorithm here

    print('training dataset to SVD')
    algo.train(dataset)

    print('done...')

    # this curator has no recommendations for this tag,
    # so the prediction should be their rating
    user = '11978515'
    tag = 'Sniper'

    print(algo.predict(user, tag, r_ui=1, verbose=True))
