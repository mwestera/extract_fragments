import glob
import os
import random
import nltk.data
from extract_various_fragments import utils
import csv
import pandas
import xml.etree.ElementTree

data_paths = {'lambada': '/home/u148187/datasets/LAMBADA',
         'personabank': '/home/u148187/datasets/personaBank-v1/original',
         'rocstories': '/home/u148187/datasets/ROCStories_winter2017.csv',
         'cmusummaries': '/home/u148187/datasets/CMU-MovieSummaries',
         '100-word-story': '/home/u148187/datasets/100wordstory.tsv',
         'snowden': '/home/u148187/datasets/snowden_interview.txt',
          # 'reuters': '',
          'arrau-wsj': '/home/u148187/datasets/ARRAU/ARRAU-wsj_raw',
          'moviedic': '/home/u148187/datasets/MovieDiC_V2/MovieDiC_V2-cleaned.xml',
          'santabarbara': '/home/u148187/datasets/santa barbara corpus/TRN',
          'switchboard': '',
        }

random.seed(1111)

words_per_fragment = 120
min_num_sentences = 4
all_fragments = {key: [] for key in data_paths.keys()}
fragments_per_genre = 10
fragments_per_doc = 5

print('Loading fragments from various corpora...\n')

## Santa Barbara Spoken Corpus ##
paths = glob.glob(data_paths['santabarbara'] + '/*.trn')
ids = []
while len(all_fragments['santabarbara']) < fragments_per_genre:
    p = random.choice(paths)
    id = p
    if id not in ids:
        ids.append(id)
        with open(p, encoding="utf8", errors='ignore') as file:
            sentences = utils.text_to_sentences(file.read(), style='santabarbara')
            fragments = utils.divide_sentences_into_fragments(sentences, id, words_per_fragment, min_num_sentences)
            for fragment in fragments:
                if len(all_fragments['santabarbara']) < fragments_per_genre:
                    all_fragments['santabarbara'].append(fragment)


## MovieDiC
# Coarse manual cleanup:
# sed -i 's/>\&</>\&amp;</g' MovieDiC_V2.xml
# sed -i 's/ \& / \&amp; /g' MovieDiC_V2.xml
# sed -i 's/<\/movie .*/<\/movie>/g' MovieDiC_V2.xml
# sed -i 's/\&emdash;/ /g' MovieDiC_V2.xml
# sed -r -i 's/([A-Z])\&([A-Z])/\1\&amp;\2/g' MovieDiC_V2.xml       # Shouldn't there be an extra escape char since it's -r?
# sed -i 's/Ben\&Ben/Ben\&amp;Ben/g' MovieDiC_V2.xml
# sed -i 's/q\&a/q\&amp;a/g' MovieDiC_V2.xml
# sed -i 's/\&\&/\&amp;\&amp;/g' MovieDiC_V2.xml
# sed -i 's/\&<\//\&amp;<\//g' MovieDiC_V2.xml      # WARNING: Cheap fix!
# sed -i "s/\&iacute;/'/g" MovieDiC_V2.xml
# sed -i "s/\&igrave;/'/g" MovieDiC_V2.xml
# sed -i "s/\&icirc;/'/g" MovieDiC_V2.xml
# And remove some non-ASCII characters.

movies = xml.etree.ElementTree.parse(data_paths['moviedic']).getroot()
ids = []
while len(all_fragments['moviedic']) < fragments_per_genre:
    i = random.randint(0, len(movies)-1)
    j = random.randint(0, len(movies[i])-1)
    id = 'moviedic:'+str(movies[i].attrib['id'])+str(movies[i][j].attrib['id'])
    if id not in ids:
        ids.append(id)
        text = ''
        for item in movies[i][j]:
            if item.tag == 'speaker':
                text += ' '.join([n.capitalize() for n in item.text.split()]) + ': '
            if item.tag == 'utterance':
                text += item.text + '\n'
        sentences = utils.text_to_sentences(text.strip(), style='moviedic')
        fragments = utils.divide_sentences_into_fragments(sentences, id, words_per_fragment, min_num_sentences)
        for fragment in fragments:
            if len(all_fragments['moviedic']) < fragments_per_genre:
                all_fragments['moviedic'].append(fragment)

## LAMBADA fragments ##
paths = glob.glob(data_paths['lambada'] + '/train-novels' + '/**/*.txt', recursive=True)
# if len(paths) < 1000:
    # print('Warning: You are currently using a smaller subset of LAMBADA.')
ids = []
while len(all_fragments['lambada']) < fragments_per_genre:
    p = random.choice(paths)
    id = p
    if id not in ids:
        ids.append(id)
        with open(p) as file:
            sentences = utils.text_to_sentences(file.read(), style='lambada', max=100)
            fragments = utils.divide_sentences_into_fragments(sentences, id, words_per_fragment, min_num_sentences)
            for fragment in fragments:
                if len(all_fragments['lambada']) < fragments_per_genre:
                    all_fragments['lambada'].append(fragment)

## PersonaBank stories ##
paths = glob.glob(data_paths['personabank'] + '/**/*.txt', recursive=True)
ids = []
while len(all_fragments['personabank']) < fragments_per_genre:
    p = random.choice(paths)
    id = p
    if id not in ids:
        ids.append(id)
        with open(p) as file:
            sentences = utils.text_to_sentences(file.read(), style='personabank')
            fragments = utils.divide_sentences_into_fragments(sentences, id, words_per_fragment, min_num_sentences)
            for fragment in fragments:
                if len(all_fragments['personabank']) < fragments_per_genre:
                    all_fragments['personabank'].append(fragment)

## ROC stories ##
with open(data_paths['rocstories']) as file:
    rows = [row for row in csv.reader(file)]
    ids = []
    while len(all_fragments['rocstories']) < fragments_per_genre:
        row = random.choice(rows)
        id = data_paths['rocstories'] + ':' + row[0] + '-' + row[1]
        if id not in ids:
            ids.append(id)
            sentences = utils.text_to_sentences(' '.join(row[2:]), style='rocstories')
            fragments = utils.divide_sentences_into_fragments(sentences, id, words_per_fragment, min_num_sentences)
            for fragment in fragments:
                if len(all_fragments['rocstories']) < fragments_per_genre:
                    all_fragments['rocstories'].append(fragment)



## 100-word-story.org
with open(data_paths['100-word-story']) as file:
    rows = [row for row in csv.reader(file, delimiter='\t')]
    ids = []
    while len(all_fragments['100-word-story']) < fragments_per_genre:
        row = random.choice(rows)
        id = data_paths['100-word-story'] + ':' + row[0].replace(' ', '_') + '-' + row[1].replace(' ', '_')
        if id not in ids:
            ids.append(id)
            sentences = utils.text_to_sentences(' '.join(row[2:]), style='100-word-story')
            fragments = utils.divide_sentences_into_fragments(sentences, id, words_per_fragment, min_num_sentences)
            for fragment in fragments:
                if len(all_fragments['100-word-story']) < fragments_per_genre:
                    all_fragments['100-word-story'].append(fragment)


## CMU movie summaries ##
with open(os.path.join(data_paths['cmusummaries'], 'plot_summaries.txt')) as file:
    with open(os.path.join(data_paths['cmusummaries'], 'movie.metadata.tsv')) as file_meta:
        meta = pandas.read_csv(file_meta, delimiter='\t', header=None)
        rows = [row for row in csv.reader(file, delimiter='\t')]
        ids = []
        while len(all_fragments['cmusummaries']) < fragments_per_genre:
            row = random.choice(rows)
            id = data_paths['cmusummaries'] + ':' + row[0]
            if id not in ids and \
                    'English' in meta.loc[meta[0] == int(row[0])][6].values[0] and \
                    float(meta.loc[meta[0] == int(row[0])][5].values[0]) < meta[5].mean():
                ids.append(id)
                sentences = utils.text_to_sentences(' '.join(row[1:]), style='cmusummaries')
                fragments = utils.divide_sentences_into_fragments(sentences, id, words_per_fragment, min_num_sentences)
                for fragment in fragments:
                    if len(all_fragments['cmusummaries']) < fragments_per_genre:
                        all_fragments['cmusummaries'].append(fragment)

## Snowden interview ##
# From the transcript, take up to as many fragments as allowed.
with open(data_paths['snowden']) as file:
    sentences = utils.text_to_sentences(file.read(), style='snowden')
    fragments = utils.divide_sentences_into_fragments(sentences, data_paths['snowden'], words_per_fragment, min_num_sentences)
    for fragment in fragments:
        if len(all_fragments['snowden']) < fragments_per_genre:
            all_fragments['snowden'].append(fragment)

## Switchboard ##
switchboard_discourses = nltk.corpus.switchboard.discourses()
ids = []
while len(all_fragments['switchboard']) < fragments_per_genre:
    i = random.randint(0, len(switchboard_discourses)-1)
    id = 'switchboard:'+str(i)
    if id not in ids:
        ids.append(id)
        text = '\n'.join([turn.speaker + ': ' + ' '.join(turn[0:]) + '.' for turn in switchboard_discourses[i]])
        sentences = utils.text_to_sentences(text, style='switchboard')
        fragments = utils.divide_sentences_into_fragments(sentences, id, words_per_fragment, min_num_sentences)
        for fragment in fragments:
            if len(all_fragments['switchboard']) < fragments_per_genre:
                all_fragments['switchboard'].append(fragment)

## ARRAU wall street journal section:
paths = glob.glob(data_paths['arrau-wsj'] + '/*')
ids = []
while len(all_fragments['arrau-wsj']) < fragments_per_genre:
    p = random.choice(paths)
    id = p
    if id not in ids:
        ids.append(id)
        with open(p) as file:
            sentences = utils.text_to_sentences(file.read(), style='arrau-wsj')
            fragments = utils.divide_sentences_into_fragments(sentences, id, words_per_fragment, min_num_sentences)
            for fragment in fragments:
                if len(all_fragments['arrau-wsj']) < fragments_per_genre:
                    all_fragments['arrau-wsj'].append(fragment)

# # Reuters; replaced by ARRAU-wsj
# ids = []
# while len(all_fragments['reuters']) < fragments_per_genre:
#     file_id = random.choice(nltk.corpus.reuters.fileids())
#     id = 'reuters:'+file_id
#     if id not in ids:
#         ids.append(id)
#         text = nltk.corpus.reuters.raw(file_id)
#         sentences = utils.text_to_sentences(text, style='reuters')
#         fragments = utils.divide_sentences_into_fragments(sentences, id, words_per_fragment, min_num_sentences)
#         for fragment in fragments:
#             if len(all_fragments['reuters']) < fragments_per_genre:
#                 all_fragments['reuters'].append(fragment)

# TODO (low priority) Film Corpus 2.

# PRINTING just to test ##
for key in all_fragments.keys():
    print('===========',key,'===========')
    for fragment in all_fragments[key]:
         print(fragment.pretty_string(header=True))

for key in all_fragments.keys():
    print(key + ':', len(all_fragments[key]))
