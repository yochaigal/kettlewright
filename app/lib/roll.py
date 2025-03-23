import random

def roll_dice(face):
    number = random.randint(1,face)
    return number

def roll_multi_dice(face, count):
    results = []
    total = 0
    for _ in range(count):
        number = random.randint(1,face)
        results.append(number)
        total += number
    return results, total

def roll_list(list):
    num = roll_dice(len(list))
    return list[num-1]

def roll_dict(dict):
    keys = []
    for x in dict:
        keys.append(x)
    k = keys[random.randint(0, len(keys)-1)]
    return k, dict[k]