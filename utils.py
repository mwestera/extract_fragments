import nltk.data
import re
import textwrap
import random


headers = ['prologue', 'introduction', 'chapter one', 'part one', 'chapter 1', 'part 1', 'part i', 'chapter i']
headers_num = ['chapter', 'section', 'part']

with open('data/names.txt') as namesfile:
    NAMES = [name.strip() for name in namesfile.readlines()]

class Sentence:

    def __init__(self, words, speaker=None):
        self.speaker = speaker
        self.words = words

    def toString(self, inc_speaker=True):
        return '{}: {}'.format(self.speaker, self.words)

class Fragment:

    def __init__(self, sentences, identifier, start=0, end=0, title=None):
        self.start = start
        self.end = end
        self.sentences = sentences
        self.identifier = identifier
        self.title = title
        # TODO Add possible cutoffs as a parameter? Or make a [fragment + cutoff] the main unit?

        self.num_words = 0
        for sent in sentences:
            self.num_words += word_count(sent.words)


    def pretty_string(self, indices=None, header=False):
        if indices is None:
            indices = (0, len(self.sentences))
        s = ''
        if header:
            s += '----------- fragment ----------\n'
            s += 'source: {0} ({2}-{3})\nlength: {1} words\n'.format(self.identifier,
                                                                     self.num_words,
                                                                     self.start,
                                                                     self.end,
                                                                     )
            s += '- - - - - - - - - - - - - - - -\n'
        textbuffer = ''
        speaker = None
        for sent in self.sentences[indices[0]:indices[1]]:
            if sent.speaker is None or sent.speaker == speaker:
                textbuffer += sent.words + ' '
            else:
                # If there was a previous utterance, first spell out the buffer
                if speaker is not None:
                    s += self.wrap(textbuffer, speaker=speaker) + '\n'
                speaker = sent.speaker
                textbuffer = sent.words + ' '
        s += self.wrap(textbuffer, speaker=speaker) + '\n'
        if header:
            s += '-------------------------------\n'

        return s

    def wrap(self, text, speaker=None):
        s = ''
        if speaker is None:
            s += textwrap.fill(text, 80)
        else:
            text = textwrap.fill(text, 80 - len(speaker + ': '))
            for i, line in enumerate(text.splitlines(keepends=True)):
                if i == 0:
                    s += speaker + ': '
                else:
                    s += ' ' * len(speaker + ': ')
                s += line
        return s


def word_count(s):
    return len(re.findall(r'\w+', s))


def word_gen(file):
    for line in file:
        for word in line.split():
            yield word


def remove_front_matter(sentences, style):
    cleaned = []
    if style == 'lambada':
        indicators = ['published', 'publisher', 'author', 'novel', 'copyright', '©',
                       'edition', 'ebook', 'licensed', 'licence', 'information', 'address',
                       'purchase', 'isbn', 'disclaimer', 'publication', 'publications',
                       'rights', 'fictional', 'fictitious', 'book', 'www', 'draft',
                       'dedicate', 'dedicated', 'reproduced', 'reproduction', 'reproduce',
                       'semblance', 'resemblance', 'wife', 'husband', '**', 'fiction', '_____']
    if style == 'cmusummaries':
        indicators = ['book', 'novel', 'movie', 'film', 'director']
    for sent in sentences:
        stop = False
        for i in indicators:
            if i in sent:
                stop = True
                break
        if sent.strip().startswith('by'):
            stop = True
        if not stop:
            cleaned.append(sent)
    return cleaned


def remove_headers(sentences):
    # TODO improve this
    cleaned = []
    for sentence in sentences:
        for h in headers:
            sentence = sentence.replace(h + ' ', '')
        # for h in headers_num:
        #     if sentence.startswith(h):
        #         cleaned.append(sentence[len(h)+3:])
        #         break
        cleaned.append(sentence)
    return cleaned


def despace_quotation_marks(s):
    despaced = ''
    i = 0
    quote = False
    while i < len(s):
        if s[i] == '\"':
            if quote:
                despaced = despaced[:-1] # remove last space
                despaced += s[i]         # push " close.
                i += 1
            else:
                despaced += s[i]        # keep last space, push " open, ignore next space.
                i += 2
            quote = not quote
        else:
            despaced += s[i]
            i += 1
    return despaced

def remove_spoken_markup(s):
    ## Based on Santa Barbara Spoken Corpus Annotation Guideline
    # remove everything in parentheses:
    s = re.sub(r'\([^)]*\)', '', s)
    # remove square brackets with numbers:
    s = re.sub(r'\[\d', '', s)
    s = re.sub(r'\d\]', '', s)
    # remove angles with caps:
    s = re.sub(r'<[A-Z]*', '', s)
    s = re.sub(r'[A-Z]*>', '', s)
    s = re.sub(r'<L\d', '', s)
    s = re.sub(r'L\d>', '', s)
    # Remove other simple stuff:
    markup_to_remove = ['--', '[', ']', '\\', '/', '-', '^', '!', '=', '\\/', '/\\', '...', '..', '@', '%', '<@', '@>', 'X', '&', '|', '<|', '|>', '<', '>', ')']
    s = '\n'.join([line for line in s.split('\n') if not line.startswith('$')])
    for markup in markup_to_remove:
        s = s.replace(markup, '')
    s = re.sub(' +', ' ', s)    # remove multi-spaces introduced above
    return s

def untokenize(tokens_or_string):
    ## Not satisfied with the following:
    """
    Untokenizing a text undoes the tokenizing operation, restoring
    punctuation and spaces to the places that people expect them to be.
    Ideally, `untokenize(tokenize(text))` should be identical to `text`,
    except for line breaks.
    From https://github.com/commonsense/metanl/blob/master/metanl/token_utils.py .
    """
    # text = ' '.join(words)
    # step1 = text.replace("`` ", '"').replace(" ''", '"').replace('. . .',  '...')
    # step2 = step1.replace(" ( ", " (").replace(" ) ", ") ")
    # step3 = re.sub(r' ([.,:;?!%]+)([ \'"`])', r"\1\2", step2)
    # step4 = re.sub(r' ([.,:;?!%]+)$', r"\1", step3)
    # step5 = step4.replace(" '", "'").replace(" n't", "n't").replace(
    #      "can not", "cannot")
    # step6 = step5.replace(" ` ", " '")
    # return step6.strip()

    ## Not satisfied with the following:
    # mt = MosesTokenizer()
    # md = MosesDetokenizer()
    # sentences = [truecase(md.detokenize(mt.tokenize(sentence))) for sentence in sentences]
    # sentences = [truecase(untokenize(sentence.split(' '))) for sentence in sentences]

    s = ' '.join(tokens_or_string) if isinstance(tokens_or_string, list) else tokens_or_string
    s = truecase(s)
    s = s.replace(' i ', ' I ')
    s = s.replace(' \'s ', '\'s ')
    s = s.replace(' \'re ', '\'re ')
    s = s.replace(' \'m ', '\'m ')
    s = s.replace(' \'ve ', '\'ve ')
    s = s.replace(' n\'t', 'n\'t')
    s = s.replace(' \'d', '\'d')
    s = s.replace(' ,', ',')
    s = s.replace(' .', '.')
    s = s.replace(' ;', ';')
    s = s.replace(' :', ':')
    s = s.replace(' !', '!')
    s = s.replace(' ?', '?')
    s = s.replace(' )', ')')
    s = s.replace('( ', '(')
    # s = s.replace('` ', '`')
    # s = s.replace(' \'', '\'')
    s = s.replace('\'\'', '\"')
    s = s.replace('``', '\"')
    s = s.replace('`', '\'')
    s = despace_quotation_marks(s)

    return s

def truecase(text):
    # TODO Improve; still unreliable.
    """From user tobigue on https://stackoverflow.com/questions/7706696/how-can-i-best-determine-the-correct-capitalization-for-a-word"""
    # apply POS-tagging
    tagged_sent = nltk.pos_tag([word.lower() for word in nltk.word_tokenize(text)])
    # infer capitalization from POS-tags
    normalized_sent = [w.capitalize() if t in ["NNP"] else w for (w, t) in tagged_sent]
    # capitalize first word in sentence
    normalized_sent[0] = normalized_sent[0].capitalize()
    # use regular expression to get punctuation right
    pretty_string = ' '.join(normalized_sent)
        # re.sub(" (?=[\.,'!?:;])", "", ' '.join(normalized_sent))
    # pretty_string.capitalize()
    return pretty_string


def text_to_sentences(text, style, max=-1):
    sent_tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')

    if style in ['personabank', 'rocstories', '100-word-story', 'cmusummaries', 'reuters', 'lambada', 'arrau-wsj']:
        if style == 'arrau-wsj':
            text = '\n'.join(text.split('\n')[1:])
        sents = sent_tokenizer.tokenize(text)
        if max > 0:
            sents = sents[:max]
        if style == 'lambada':
            sents = remove_front_matter(sents, style)
            sents = remove_headers(sents)
            sents = [untokenize(s) for s in sents]
        if style == 'cmusummaries':
            sents = remove_front_matter(sents, style)
        if style == 'reuters':
            if sents[0].isupper():
                sents = []  # Remove any message starting with ALL CAPS
        sents = [Sentence(s) for s in sents]
    if style == 'santabarbara':
        text2 = ''
        prev_speaker = ''
        for line in text.split('\n'):
            line = line.split('\t')
            if len(line) >= 4:
                sp = line[2].capitalize().strip().replace(':', '')
                line = remove_spoken_markup(line[3]).strip()
                if len(line) > 1:
                    if sp == '' or sp == prev_speaker:
                        text2 += ' ' + line
                    else:
                        text2 += '\n' + sp + ': ' + line
                        prev_speaker = sp
        text = text2.strip()
    if style in ['snowden', 'switchboard', 'moviedic', 'santabarbara']:
        speaker_map = {}
        sents = []
        for line in text.split('\n\n' if style == 'snowden' else '\n'):
            line_split = line.replace('\n',' ').split(':')  # to isulate speaker
            tokens = [line_split[0]]
            for rest in line_split[1:]:
                tokens.extend(rest.split())
            if len(tokens) >= 2:
                speaker = tokens[0].replace(':','')
                if style == 'switchboard':
                    if speaker not in speaker_map:
                        while True:
                            random_speaker = random.choice(NAMES)
                            if random_speaker not in speaker_map.values():
                                break
                        speaker_map[speaker] = random_speaker
                    speaker = speaker_map[speaker]
                text = ' '.join(tokens[1:])
                sentences = sent_tokenizer.tokenize(text)
                if style == 'switchboard':
                    sentences = [untokenize(s) for s in sentences]
                sents += [Sentence(s, speaker=speaker) for s in sentences]

        # TODO: Abbreviations are cut up... at least in switchboard (U.S., discourse on puerto rico). Whenever single line X., append to previous?
        # TODO: Camera instructions? Whenever a portion is all caps, or contains camera, panning, close shot (broken up as Close: shot), Med. shot, quick shot, quick close shot...
        # TODO For switchboard, a lot of `..' and `,.' and `?.' remain.
        # TODO The ACTIVISTS are all exchanging puzzled looks. (moviedic_0_85)

    return sents


def divide_sentences_into_fragments(sentences, identifier, words_per_fragment, min_num_sentences, words_overlap=-1):

    if words_overlap == -1:
        words_overlap = words_per_fragment/2

    fragments = []
    fragment1 = []
    start1 = -1
    nwords1 = 0
    fragment2 = []
    start2 = -1
    nwords2 = 0
    fragment_already_pushed = False

    for i, s in enumerate(sentences):

        if start1 == -1:
            start1 = i

        fragment1.append(s)
        nwords1 += word_count(s.words)

        if nwords1 >= words_per_fragment:
            fragments.append(Fragment(fragment1, identifier, start=start1, end=i))
            fragment_already_pushed = True
            fragment1, start1, nwords1 = fragment2, start2, nwords2
            fragment2, start2, nwords2 = [], -1, 0

        if nwords1 >= words_per_fragment - words_overlap:
            if start2 == -1:
                start2 = i
            fragment2.append(s)
            nwords2 += word_count(s.words)

        if i == len(sentences)-1 and not fragment_already_pushed:
            fragments.append(Fragment(fragment1, identifier, start=start1, end=i))

    # Delete those with too few sentences
    fragments = [fragment for fragment in fragments if len(fragment.sentences) >= min_num_sentences]

    return fragments