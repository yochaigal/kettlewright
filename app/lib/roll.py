import random

def roll_dice(face):
    number = random.randint(1,face)
    return number

def roll_list(list):
    num = roll_dice(len(list))
    return list[num-1]