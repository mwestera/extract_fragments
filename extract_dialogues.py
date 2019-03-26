import glob
import os
import random
import nltk.data
import nltk.tokenize
import utils
import csv
import xml.etree.ElementTree

import re

data_paths = {'lambada': '/home/u148187/datasets/LAMBADA',
         'personabank': '/home/u148187/datasets/personaBank-v1/original',
         'rocstories': '/home/u148187/datasets/ROCStories_winter2017.csv',
         'cmusummaries': '/home/u148187/datasets/CMU-MovieSummaries',
         '100-word-story': '/home/u148187/datasets/100wordstory.tsv',
         'snowden': '/home/u148187/datasets/snowden_interview.txt',
          # 'reuters': '',
          'arrau-wsj': '/home/u148187/datasets/ARRAU/ARRAU-wsj_raw',
          'moviedic': '/home/u148187/datasets/MovieDiC_V2/MovieDiC_V2.xml',
          'santabarbara': '/home/u148187/datasets/santa barbara corpus/TRN',
          'switchboard': '',
          'bookcorpus': '/home/u148187/datasets/bookcorpus/out_txts/',
        }

# TODO also do gutenberg and books corpus.
# TODO Also include '/home/u148187/datasets/Film Corpus v2  imsdb /imsdb_scenes_dialogs_nov_2015/*.txt'

N_ADV_QUESTIONS = 20
DISCOURSE_LENGTH = 10
MIN_DIALOGUE_LENGTH = 10

OUT_CSV_BOOKS = 'data/dialogues_bookcorpus.csv'
OUT_CSV_LAMBADA = 'data/dialogues_lambada.csv'
OUT_CSV_MOVIEDIC = 'data/dialogues_moviedic.csv'
OUT_CSV_BOOKS_PLAIN = 'data/all_dialogues_bookcorpus.csv'
OUT_CSV_LAMBADA_PLAIN = 'data/all_dialogues_lambada.csv'
OUT_CSV_MOVIEDIC_PLAIN = 'data/all_dialogues_moviedic.csv'

INTER_DIALOGUE_DISTANCE = 150       # chars

def question_based_fragments(dialogues, question_ids):
    fragments = []
    if len(question_ids) < N_ADV_QUESTIONS + 1:
        return fragments
    if len(dialogues) == 0:
        return fragments
    for qid in question_ids:
        if qid[1] > DISCOURSE_LENGTH and \
                qid[1] < len(dialogues[qid[0]])-1 and \
                len(dialogues[qid[0]]) >= DISCOURSE_LENGTH+2 and \
                '?' not in dialogues[qid[0]][qid[1]-1][-5:] and \
                '?' not in dialogues[qid[0]][qid[1]+1][-5:]:
            adv_question_ids = []
            while len(adv_question_ids) < N_ADV_QUESTIONS:
                idx = random.choice(question_ids)
                if idx != qid:
                    adv_question_ids.append(idx)
            adv_questions = [dialogues[id[0]][id[1]] for id in adv_question_ids]

            fragment = (dialogues[qid[0]][qid[1]-DISCOURSE_LENGTH:qid[1]],
                        dialogues[qid[0]][qid[1]],
                        dialogues[qid[0]][qid[1]+1],
                        adv_questions)

            fragments.append(fragment)

    return fragments

def extract_dialogues(text):
    quote_pattern = '("|“)([^("|”)]*)[^ ]("|”)'

    # newlines = '\n' in text     # TODO Use the meaningful newlines in bookcorpus and gutenberg; if they're consistent

    dialogues = []
    question_ids = []

    current_dialogue = []
    current_question_ids = []
    current_end = 0
    for match in re.finditer(quote_pattern, text + INTER_DIALOGUE_DISTANCE * '  ' + '"0000"'):  # Ugly way of getting final dialogue pushed
        start, end = match.start(), match.end()
        quote = match.group(0).strip("\"“”")
        is_genuine_quote = True  # TODO safety check for missing quotations, e.g., newline in between?
        if is_genuine_quote:
            if start - current_end > INTER_DIALOGUE_DISTANCE:  # If new dialogue
                # Always save old (it's a dialogue after all, even if it contains e.g. no questions)
                dialogues.append(current_dialogue)
                question_ids.extend(current_question_ids)
                current_dialogue = []
                current_question_ids = []
            current_dialogue.append(quote)
            if '?' in quote[-3:] and len(quote) < 100:
                current_question_ids.append((len(dialogues), len(current_dialogue)-1))
            current_end = end

    # TODO treat    ,' abc.    as .'

    return dialogues, question_ids


# with open('/home/u148187/datasets/bookcorpus/out_txts/152__princess-electra.txt') as file:
#     extract_dialogues(file.read(), debug=True)


def extract_dialogues_smarter(path, min_dialogue_spacing, min_length):
    quote_pattern = '("|“)([^("|”)]*)[^ ]("|”)'

    with open(path) as file:

        previous_end_idx = 0
        total_idx = 0

        all_dialogues = []
        all_question_ids = []

        current_dialogue = []
        current_question_ids = []

        for i, line in enumerate(file):

            current_turn = []

            for j, match in enumerate(re.finditer(quote_pattern, line)):
                current_start_idx = total_idx + match.start(0)

                if (current_start_idx - previous_end_idx) >= min_dialogue_spacing:
                    # It might be neat to check independently for INTER_TURN_DISTANCE as well,
                    # but I'm assuming turns are always delineated by newlines OR new dialogues.
                    if current_turn != []:
                        current_dialogue.append(current_turn)
                        current_turn = []
                    if len(current_dialogue) >= min_length:
                        all_dialogues.append(current_dialogue)
                    current_dialogue = []

                quote = match.group(0).strip("\"“”")

                # For constructions like '"Blablabla," he said.'
                if quote.endswith(','):
                    next_period = re.search('\.', line[match.end()+1:])      # TODO Problem: ...said Dr. Dre...
                    next_quote = re.search(quote_pattern, line[match.end()+1:])
                    if next_period is None or next_quote is None or next_period.start() < next_quote.start():
                        quote = quote[:-1] + '.'

                # Append to current turn
                current_turn.append(quote)
                previous_end_idx = total_idx + match.end()

            # If there was a turn, append it to the dialogue
            if current_turn != []:
                current_dialogue.append(current_turn)

            total_idx += len(line)

        # If there was a dialogue, append it to the dialogues
        if len(current_dialogue) >= min_length:
            all_dialogues.append(current_dialogue)

    return all_dialogues

# bookcorpus_paths = glob.glob(data_paths['bookcorpus'] + '/*.txt')
# min_dialogue_spacing = 200
# min_length = 2
# out_file = 'output/bookcorpus_dialogues_{}_{}.csv'.format(min_dialogue_spacing, min_length)
# if os.path.exists(out_file):
#     if not input('Output file already exists. Overwrite?').startswith("y"):
#         quit()
# with open(out_file, 'w') as output:
#     writer = csv.writer(output);
#     for i, path in enumerate(bookcorpus_paths):
#         print('Book', i, 'of', len(bookcorpus_paths))
#         all_dialogues = extract_dialogues_smarter(path, min_dialogue_spacing, min_length)
#         for dia in all_dialogues:
#             writer.writerow([os.path.basename(path)[:-4]] + [' '.join(turn) for turn in dia])



def fragment_to_csv(fragment, id, out):
    wr = csv.writer(open(out, 'a'))
    as_list = [s for s in fragment[0]] + [fragment[1]] + [fragment[2]] + [s for s in fragment[3]] + [id]
    wr.writerow(as_list)

def dialogue_to_csv(dialogue, id, out):
    wr = csv.writer(open(out, 'a'))
    wr.writerow(dialogue + [id])


def fragments_from_bookcorpus():
    # BookCorpus fragments ##
    if os.path.exists(OUT_CSV_BOOKS) or os.path.exists(OUT_CSV_BOOKS_PLAIN):
        if input('Output files already exist. Overwrite?').startswith("n"):
            quit()
    open(OUT_CSV_BOOKS, 'w').close()      # WARNING, only for testing!
    open(OUT_CSV_BOOKS_PLAIN, 'w').close()      # WARNING, only for testing!
    paths = glob.glob(data_paths['bookcorpus'] + '/*.txt')
    print('BookCorpus: checking {} books.'.format(len(paths)))
    for pidx, p in enumerate(paths):
        with open(p) as file:
            print('[{}/{}]'.format(pidx, len(paths)), 'searching', p)
            text = file.read().replace('\n',' ')    # TODO At some point use information contained in newlines (turn taking)
            dialogues, question_ids = extract_dialogues(text)

        fragments_for_book = question_based_fragments(dialogues, question_ids)
        # all_fragments['bookcorpus'].extend(fragments_for_book)
        for fragment in fragments_for_book:
            fragment_to_csv(fragment, 'BookCorpus/' + os.path.basename(p), OUT_CSV_BOOKS)
        for dialogue in dialogues:
            if len(dialogue) > MIN_DIALOGUE_LENGTH:
                 dialogue_to_csv(dialogue, 'BookCorpus/' + os.path.basename(p), OUT_CSV_BOOKS_PLAIN)

    # Use Quote Attribution from StanfordNLP; Nah it takes long and has very buggy results.


## MovieDIC corpus
def fragments_from_moviedic():
    if os.path.exists(OUT_CSV_MOVIEDIC) or os.path.exists(OUT_CSV_MOVIEDIC_PLAIN):
        if input('Output files already exist. Overwrite?').startswith("n"):
            quit()
    open(OUT_CSV_MOVIEDIC, 'w').close()      # WARNING, only for testing!
    open(OUT_CSV_MOVIEDIC_PLAIN, 'w').close()      # WARNING, only for testing!
    movies = xml.etree.ElementTree.parse(data_paths['moviedic']).getroot()
    print('MovieDIC corpus: checking {} movies.'.format(len(movies)))
    for i in range(len(movies)):
        dialogues = []
        question_ids = []
        n_dialogue = 0
        for j in range(len(movies[i])):
            dialogue = []
            n_turn = 0
            speaker = None
            for item in movies[i][j]:
                if item.tag == 'speaker':
                    speaker = ' '.join([n.capitalize() for n in item.text.split()])
                if item.tag == 'utterance':
                    utterance = item.text.strip()
                    # dialogue.append((speaker, utterance))     # TODO currently ignores speakers...
                    dialogue.append(utterance)
                    if '?' in utterance[-3:] and len(utterance) < 100:
                        question_ids.append((n_dialogue,n_turn))
                    n_turn += 1
            dialogues.append(dialogue)
            n_dialogue += 1

        fragments_for_movie = question_based_fragments(dialogues, question_ids)
        for fragment in fragments_for_movie:
            fragment_to_csv(fragment, 'MovieDIC/{}'.format(i), OUT_CSV_MOVIEDIC)
        for dialogue in dialogues:
            if len(dialogue) > MIN_DIALOGUE_LENGTH:
                dialogue_to_csv(dialogue, 'MovieDIC/{}'.format(i), OUT_CSV_MOVIEDIC_PLAIN)


## LAMBADA fragments ##
def fragments_from_lambada():
    if os.path.exists(OUT_CSV_LAMBADA) or os.path.exists(OUT_CSV_LAMBADA_PLAIN):
        if input('Output files already exist. Overwrite?').startswith("n"):
            quit()
    open(OUT_CSV_LAMBADA, 'w').close()      # WARNING, only for testing!
    open(OUT_CSV_LAMBADA_PLAIN, 'w').close()      # WARNING, only for testing!
    paths = glob.glob(data_paths['lambada'] + '/train-novels' + '/**/*.txt', recursive=True)
    if len(paths) < 1000:
        print('Warning: You are currently using a smaller subset of LAMBADA.')
    print('LAMBADA: checking {} books.'.format(len(paths)))
    for pidx, p in enumerate(paths):

        print('[{}/{}]'.format(pidx, len(paths)), 'searching', p)

        with open(p) as file:
            text = ' '.join([sent.words for sent in utils.text_to_sentences(file.read(), style='lambada')])

            dialogues, question_ids = extract_dialogues(text)

        fragments_for_book = question_based_fragments(dialogues, question_ids)

        for fragment in fragments_for_book:
            id = p.split('/')
            id = id[0] + '/' + id[1]
            fragment_to_csv(fragment, 'LAMBADA/' + id, OUT_CSV_LAMBADA)
        for dialogue in dialogues:
            if len(dialogue) > MIN_DIALOGUE_LENGTH:
                dialogue_to_csv(dialogue, 'LAMBADA/' + id, OUT_CSV_LAMBADA_PLAIN)


# WARNING: This also removes capitalization etc... Required for SkipThought I guess?
def rewrite_tokenized_sentence_based(csv_src):
    csvreader = csv.reader(open(csv_src))
    csvwriter = csv.writer(open(csv_src[:-4]+'-SENT.csv', 'a'))           # TODO What if file already exists?

    for i, row in enumerate(csvreader):
        # print('Tokenizing row', i, 'of', csv_src)

        discourse = ' '.join(row[:DISCOURSE_LENGTH]).lower()
        discourse_sents = nltk.tokenize.sent_tokenize(discourse)
        question_sents = nltk.tokenize.sent_tokenize(row[DISCOURSE_LENGTH])
        answer_sents = nltk.tokenize.sent_tokenize(row[DISCOURSE_LENGTH+1])

        if len(answer_sents) > 0:       # Weirdly necessary

            adv_questions = row[DISCOURSE_LENGTH+2:-1]
            adv_questions_sents = [nltk.tokenize.sent_tokenize(question) for question in adv_questions]

            answer_cut = answer_sents[0]
            question_cut = question_sents[-1]
            discourse_cut = (discourse_sents + question_sents[:-1])[-DISCOURSE_LENGTH:]
            adv_questions_sents_cut = [sents[-1] for sents in adv_questions_sents]

            answer_cut_tokenized = ' '.join(nltk.tokenize.word_tokenize(answer_cut))
            question_cut_tokenized = ' '.join(nltk.tokenize.word_tokenize(question_cut))
            discourse_cut_tokenized = [' '.join(nltk.tokenize.word_tokenize(sent)) for sent in discourse_cut]
            adv_questions_sents_cut_tokenized = [' '.join(nltk.tokenize.word_tokenize(sent)) for sent in adv_questions_sents_cut]

            as_list = discourse_cut_tokenized + [question_cut_tokenized] + [answer_cut_tokenized] + adv_questions_sents_cut_tokenized + [row[-1]]

            if len(row) == len(as_list):
                csvwriter.writerow(as_list)

        else:
            print('oops, empty answer string in row', i, '; ignoring, moving on!')


def prepare_for_BERT_baseline(csv_src, n_adv_questions):
    csvreader = csv.reader(open(csv_src))

    print("Composing QA and AQ items...")

    # first gather all questions
    questions = []
    QA_items = []
    AQ_items = []
    for i, row in enumerate(csvreader):
        row = row[1:]
        for j, item in enumerate(row):
            if item.endswith("?"):
                if i > 0:
                    AQ_items.append([row[j-1], row[j]])
                if i < len(row)-1:
                    QA_items.append([row[j], row[j+1]])
                questions.append(item)

    print("Writing to files... QA_items: {}, AQ_items: {}, questions: {}".format(len(QA_items), len(AQ_items), len(questions)))

    with open(csv_src[:-4] + '-BERT-AQ-{}.txt'.format(n_adv_questions), 'w+') as out_file_AQ:
        for item in AQ_items:
            adv_questions = random.sample(questions, n_adv_questions)
            for each_question in [item[1]] + adv_questions:
                out_file_AQ.write(item[0] + ' ||| ' + each_question + '\n')

    with open(csv_src[:-4] + '-BERT-QA-{}.txt'.format(n_adv_questions), 'w+') as out_file_QA:
        for item in QA_items:
            adv_questions = random.sample(questions, n_adv_questions)
            for each_question in [item[0]] + adv_questions:
                out_file_QA.write(each_question + ' ||| ' + item[1] + '\n')

prepare_for_BERT_baseline('output/bookcorpus_dialogues_200_2.csv', 20)

# fragments_from_bookcorpus()

# rewrite_tokenized_sentence_based('output/dialogues_bookcorpus-len5.csv')

def newline_sentences_for_BERT(csv_src, separator=True, id_last=False):

    csvreader = csv.reader(open(csv_src))
    with open(csv_src[:-4]+'-BERT.txt', 'w+') as out_file:

        for i, row in enumerate(csvreader):
            if i % 100 == 0:
                print('Sententializing rows {0}++ of {1}'.format(i, csv_src))
            if i > 0:
                out_file.write('\n\n' if separator else '\n')
            if id_last:
                row = row[:-1]
            else:
                row = row[1:]
            dialogue = ' '.join(row)
            sents = nltk.tokenize.sent_tokenize(dialogue)
            out_file.write('\n'.join(sents))

# newline_sentences_for_BERT('output/bookcorpus_dialogues_200_5.csv', separator=True)

def newline_turns_for_BERT(csv_src, separator=True, id_last=False):
    """
    The data should be a text file in the same format as sample_text.txt
    (one sentence per line, docs separated by empty line). You can download
    an exemplary training corpus generated from wikipedia articles and splitted
    into ~500k sentences with spaCy.
    """
    csvreader = csv.reader(open(csv_src))
    with open(csv_src[:-4]+'-BERT.txt', 'w+') as out_file:

        for i, row in enumerate(csvreader):
            if i % 100 == 0:
                print('Newlining rows {0}++ of {1}'.format(i, csv_src))
            if i > 0:
                out_file.write('\n\n' if separator else '\n')
            if id_last:
                row = row[:-1]
            else:
                row = row[1:]
            out_file.write('\n'.join(row))

# newline_turns_for_BERT('output/bookcorpus_dialogues_200_5.csv', separator=False)

def extract_subtitles_xml_to_text(path):
    if os.path.isfile(path):
        paths = [path]
    else:
        paths = glob.glob(path + '/**/*.xml', recursive=True)

    regexp = re.compile("(?<=>)(.*?)(?=</w>)")

    with open('output/OpenSubtitles.txt', 'w+') as out_file:
        for i, path in enumerate(paths):
            if i != 0:
                out_file.write('\n\n')
            if i % 10 == 0:
                print('Reading subtitle {}/{}.'.format(i, len(paths)))
            with open(path, 'r') as file:
                subtitles = ' '.join(regexp.findall(file.read())).replace(' .', '.').replace(' ,', ',').replace(' !', '!').replace(' ?', '?').replace(' :', ':').replace(' ;', ';')

            sents = nltk.tokenize.sent_tokenize(subtitles)
            out_file.write('\n'.join(sents))

# extract_subtitles_xml_to_text('/home/u148187/datasets/OpenSubtitles_en')


def extract_SPICE_xml_to_text(path):
    if os.path.isfile(path):
        paths = [path]
    else:
        paths = glob.glob(path + '/**/*.xml', recursive=True)

    eventses = {}

    for path in paths:
        root = xml.etree.ElementTree.parse(path).getroot().find("basic-body")
        num_events = len(root.find("common-timeline"))
        events = [None] * num_events
        for child in root:
            if child.tag == "tier" and child.get('category') == "n":
                speaker = child.get('speaker')
                for event in child:
                    events[int(event.get("start")[1:])-1] = (speaker, event.text)

        eventses[os.path.basename(path)] = events

    return eventses

def print_SPICE_dialogue(events):
    prev_speaker = None
    prev_utterance = ""
    for e in events:
        if e is not None:
            if prev_speaker is None:
                prev_speaker = e[0]
            if e[0] == prev_speaker:
                prev_utterance += e[1]
            else:
                print(prev_speaker +":", prev_utterance)
                prev_speaker = e[0]
                prev_utterance = e[1]


# eventses = extract_SPICE_xml_to_text('/home/matthijs/datasets/SPICE-CR-XML')
#
# for key in eventses.keys():
#     print('==============================')
#     print('==========',key,'========')
#     print('==============================')
#     print_SPICE_dialogue(eventses[key])
#

