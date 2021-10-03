import random
from collections import deque
import statistics
from multiprocessing import Pool
from rng_test import Rng


def sort_master(items):
    rng = Rng(random.randint(0, 4294967295))
    channels = len(items)

    for x in range(1, channels):
        rand = rng.rngN(channels-1)+1
        print(rand)
        tmp = items[x]
        items[x] = items[rand]
        items[rand] = tmp


def shuffle(items, python_shuffle):
    if python_shuffle:
        random.shuffle(items)
    else:
        sort_master(items)
    return items


def generate_sequence(channels, packets_per_hop, python_shuffle):
    items = list(range(channels))
    items = shuffle(items, python_shuffle)

    items = [x for x in items for i in range(packets_per_hop)]
    items = deque(items)
    # random offset of the start time of the sequence
    items.rotate(random.randint(0, channels))
    items = list(items)
    return items


def run_test(radios, channels, packets_per_hop, phase, python_shuffle):
    all_sequences = [generate_sequence(
        channels, packets_per_hop, python_shuffle) for _ in range(radios)]

    seq_len = len(all_sequences[0])
    collisons = [[0 for y in range(seq_len)]
                 for x in range(radios)]

    for i in range(radios):
        for j in range(i + 1, radios):
            for k in range(len(all_sequences[i])):
                if all_sequences[i][k] == all_sequences[j][k]:
                    collisons[i][k] = 1
                    collisons[j][k] = 1

                if phase:
                    # phase difference collisions
                    # we only need to check one direction, as the other direction is the same
                    # as shifting one of the sets by 1 is the same thing
                    k_minus = (k-1) % seq_len
                    k_plus = (k+1) % seq_len
                    # i hits j's prior
                    if all_sequences[i][k_minus] == all_sequences[j][k]:
                        collisons[i][k_minus] = 1
                        collisons[j][k] = 1
                    # i hits j's next
                    if all_sequences[i][k] == all_sequences[j][k_plus]:
                        collisons[i][k] = 1
                        collisons[j][k_plus] = 1

    return collisons


def test_stats(inputs):
    radios = inputs[0]
    channels = inputs[1]
    packets_per_hop = inputs[2]
    phase = inputs[3]
    python_shuffle = inputs[4]

    total_packets = channels * packets_per_hop

    return [(total_packets - sum(y))/total_packets*100 for y in run_test(radios, channels, packets_per_hop, phase, python_shuffle)]


def run_count(radios, channels, packets_per_hop, phase, python_shuffle):
    # Adjust based on how much forking your system can handle.
    with Pool(processes=1) as pool:
        abc = pool.map(
            test_stats, [(radios, channels, packets_per_hop, phase, python_shuffle) for _ in range(1000)])
        collision_counts = []
        for x in abc:
            collision_counts.extend(x)
        print("{},{:3.2f},{:3.2f},{:3.2f},{:3.2f}".format(
            radios,
            statistics.mean(collision_counts),
            statistics.stdev(collision_counts),
            min(collision_counts),
            max(collision_counts)
        ))


if __name__ == '__main__':
    channels = 80
    packets_per_hop = 4
    min_radios = 2
    max_radios = 10
    phase = True
    python_shuffle = False

    print("radios,mean,stdev,min,max")
    for x in range(min_radios, max_radios):
        run_count(x, channels, packets_per_hop, phase, python_shuffle)
