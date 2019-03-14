import csv
import random

class FragmentLoader:


    def __init__(self, path):
        with open(path) as f:
            # self.dialogues = list(map(lambda row: row[:-1], csv.reader(f)))
            self.dialogues = list(csv.reader(f))


loader = FragmentLoader('output/dialogues_bookcorpus-len10.csv')

for d in random.sample(loader.dialogues, 100):
    print('\n'.join(d[:10]))
    print('Q:',d[10])
    print('A:', d[11])
    input('-------------- any key to continue ----------')
