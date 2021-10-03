import random
from collections import deque
import statistics
from multiprocessing import Pool
from rng_test import Rng


def sort_master(items):
    rng = Rng(random.randint(0, 4294967295), True)
    channels = len(items)

    for x in range(1, channels):
        rand = rng.rngN(channels-1)+1
        tmp = items[x]
        items[x] = items[rand]
        items[rand] = tmp


def sort_110(items):
    rng = Rng(random.randint(0, 4294967295), False)
    is_available = [True for x in range(len(items))]
    nr_fhss_entries = len(items)
    nLeft = len(is_available) - 1
    prev = 0

    sequence = [0 for _ in range(256)]

    for i in range(len(sequence)):
        if i % nr_fhss_entries == 0:
            sequence[i] = items[0]
            prev = 0
        else:
            index = prev
            while index == prev:
                c = rng.rngN(nLeft)
                index = 1
                found = 0
                while index < nr_fhss_entries:
                    if is_available[index]:
                        if found == c:
                            break
                        found += 1
                    index += 1
                if index == nr_fhss_entries:
                    index = 0
                    # print("Failed")
                    break
            sequence[i] = items[index]
            is_available[index] = False
            prev = index
            nLeft -= 1
            if nLeft == 0:
                is_available = [True for x in range(len(items))]
                nLeft = len(is_available) - 1

    # print(sequence)
    return sequence


def shuffle(items, shuffle_type):
    if shuffle_type == "Python":
        random.shuffle(items)
    if shuffle_type == "1.1.0":
        # this method always creates a 256 long list, not a multiple of the number of channels
        items = sort_110(items)
    else:
        sort_master(items)
    return items


def generate_sequence(channels, packets_per_hop, shuffle_type):
    items = list(range(channels))
    items = shuffle(items, shuffle_type)

    items = [x for x in items for i in range(packets_per_hop)]
    items = deque(items)
    # random offset of the start time of the sequence
    items.rotate(random.randint(0, len(items)))
    items = list(items)
    return items


def run_test(radios, channels, packets_per_hop, phase, shuffle_type, channel_sensitivity_width):
    all_sequences = [generate_sequence(
        channels, packets_per_hop, shuffle_type) for _ in range(radios)]

    seq_len = len(all_sequences[0])
    collisons = [[0 for y in range(seq_len)]
                 for x in range(radios)]

    for i in range(radios):
        for j in range(i + 1, radios):
            for k in range(len(all_sequences[i])):
                if abs(all_sequences[i][k] - all_sequences[j][k]) <= channel_sensitivity_width:
                    collisons[i][k] = 1
                    collisons[j][k] = 1

                if phase:
                    # phase difference collisions
                    # we only need to check one direction, as the other direction is the same
                    # as shifting one of the sets by 1 is the same thing
                    k_minus = (k-1) % seq_len
                    k_plus = (k+1) % seq_len
                    # i hits j's prior
                    if abs(all_sequences[i][k_minus] - all_sequences[j][k]) <= channel_sensitivity_width:
                        collisons[i][k_minus] = 1
                        collisons[j][k] = 1
                    # i hits j's next - i think this is equivelent to the last one when i is i + 1
                    if abs(all_sequences[i][k] - all_sequences[j][k_plus]) <= channel_sensitivity_width:
                        collisons[i][k] = 1
                        collisons[j][k_plus] = 1

    return collisons


def test_stats(inputs):
    radios = inputs[0]
    channels = inputs[1]
    packets_per_hop = inputs[2]
    phase = inputs[3]
    shuffle_type = inputs[4]
    channel_sensitivity_width = inputs[5]

    if shuffle_type == "1.1.0":
        total_packets = 256 * packets_per_hop
    else:
        total_packets = channels * packets_per_hop

    return [(total_packets - sum(y))/total_packets*100 for y in run_test(radios, channels, packets_per_hop, phase, shuffle_type, channel_sensitivity_width)]


def run_count(radios, channels, packets_per_hop, phase, shuffle_type, channel_sensitivity_width):
    # Adjust based on how much forking your system can handle.
    with Pool(processes=8) as pool:
        abc = pool.map(
            test_stats, [(radios, channels, packets_per_hop, phase, shuffle_type, channel_sensitivity_width) for _ in range(1000)])
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
    max_radios = 50
    phase = True
    shuffle_type = "Python"  # Python, 1.1.0, Master
    channel_sensitivity_width = 1  # 0 is only own channel, 1 is adjacent, etc.

    print("radios,mean,stdev,min,max")
    for x in range(min_radios, max_radios):
        run_count(x, channels, packets_per_hop, phase,
                  shuffle_type, channel_sensitivity_width)
