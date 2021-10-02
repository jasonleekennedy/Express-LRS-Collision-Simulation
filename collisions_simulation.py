import random
from collections import deque
import statistics
from multiprocessing import Pool


def generate_sequence(channels, packets_per_hop):
    items = list(range(channels))
    random.shuffle(items)
    items = [x for x in items for i in range(packets_per_hop)]
    items = deque(items)
    # random offset of the packets per channel hop
    items.rotate(random.randint(0, packets_per_hop))
    items = list(items)
    return items


def run_test(radios, channels, packets_per_hop, phase):
    all_sequences = [generate_sequence(
        channels, packets_per_hop) for _ in range(radios)]

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

    total_packets = channels * packets_per_hop

    return [(total_packets - sum(y))/total_packets*100 for y in run_test(radios, channels, packets_per_hop, phase)]


def run_count(radios, channels, packets_per_hop, phase):
    # Adjust based on how much forking your system can handle.
    with Pool(processes=8) as pool:
        abc = pool.map(
            test_stats, [(radios, channels, packets_per_hop, phase) for _ in range(1000)])
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
    channels = 20
    packets_per_hop = 4
    min_radios = 2
    max_radios = 50
    phase = True

    print("radios,mean,stdev,min,max")
    for x in range(min_radios, max_radios):
        run_count(x, channels, packets_per_hop, phase)
