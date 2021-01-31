"""
    Book reaction class
"""

import logging
import re
import time

from .configuration_loader import resource_file, load_book

wordlist = {
    'happy':    "happy day second week".split(' ') +
                "keep them wet and wait".split(' '),

    'groan':    "very long week sat".split(' ') +
                "there was no tree seen".split(' ') +
                "this is silly".split(' '),

    'excited':  "teeny green stem peeping out pot".split(' ') +
                "molly saw soft green leaf".split(' ') +
                "yippee have tree".split(' '),

    'sad':      "teeny green stem and soft green leaf had vanished".split(' ') +
                "molly was very sad".split(' ') +
                "oh dear she said".split(' ') +
                "little tear fell down her cheek".split(' '),

    'scared':   "eek molly was screaming".split(' ') +
                "three fat snails sneaking feet".split(' ')
    }

sentencelist = {
    'happy':    ["then one happy day in the second week",
                 "keep them wet and wait"],

    'groan':    ["but for one very long week the pots just sat there",
                 "there was no tree to be seen",
                 "this is silly"],

    'excited':  ["pip saw a teeny green stem peeping out of the pot",
                 "and molly saw a soft green leaf",
                 "you have a tree said mr beam"],

    'sad':      ["but the next day the teeny green stem and the soft green leaf had vanished",
                 "molly was very sad",
                 "oh dear she said and a little tear fell down her cheek"],

    'scared':   ["and if we look X molly was screaming",
                 "three fat snails were sneaking along mr mister beams feet"]
}


class Book:
    def __init__(self, source='the_teeny_tree_literal.txt'):
        self.text = load_book(resource_file(source))
        self.filtered_text = self.extract_keywords(self.text)
        self.window = (0, len(self.text))  # This window covers the possible pages where we are reading
        self.sentence = [{'text': list(dict.fromkeys(line.lower().split(' '))), 'score': 0}
                         for line in self.filtered_text]
        self.reactions = [{'idx': i, 'action': line.split(' ')[0]} for i, line in enumerate(self.text)
                          if re.search(r"^\[(.+)\]", line)]
        self.reaction_idx = 0
        self.match_thresh = 3
        self.win_size = 2
        self.expression_cooldown = 10
        self.last_expression_time = time.perf_counter()

        self.logger = logging.getLogger(name=__name__)

        self.sentences = [{'sentence': sen.split(' '), 'emotion': em}
                          for em in sentencelist for sen in sentencelist[em]]
        self.match_score_thresh = 0.5
        self.last_matched_emotion = None

    def evaluate_text_rolling_window(self, text):
        """ Work in progress: This method has not shown very good results, but there is space for improvement."""
        # Divide text into list of words, eliminate duplicates.
        text_filtered = []
        for w in text.split(' '):
            if w not in text_filtered:
                text_filtered.append(w.lower())
        # Check for matches in the current window, and update scores
        likely_idx = []
        for i in range(self.window[0], self.window[1]):
            for word in self.sentence[i]['text']:
                if word in text_filtered:
                    self.sentence[i]['score'] += 1
                    if self.sentence[i]['score'] > self.match_thresh:
                        likely_idx.append(i)
        likely_idx = list(set(likely_idx))

        # If there is no matches, let's expand the window
        if not likely_idx:
            # self.window = (max(0, self.window[0] - 1), min(len(self.text), self.window[1] + 1))
            return None

        # Once we have updated the scores, we can check in which line of the book we are in, and fit the window to the
        # most likely words to appear
        best_match = -1
        best_score = 0
        for i in reversed(likely_idx):
            if self.sentence[i]['score'] > best_score:
                best_match = i
                best_score = self.sentence[i]['score']
            self.sentence[i]['score'] = 0

        # self.window = (best_match, min(len(self.text), best_match + self.win_size))
        self.logger.debug('Window: [{}, {}]'.format(self.window[0], self.window[1]))
        self.logger.debug('Likely idxs: {}'.format(likely_idx))
        self.logger.debug('Best match, idx: {}, sentence: {}'.format(best_match, self.sentence[best_match]['text']))

        # If the most likely string contains an action, return the action and delete it from the action list
        reaction = None
        if self.reactions[self.reaction_idx]['idx'] == best_match:
            reaction = self.reactions[self.reaction_idx]['action'][1:-1]
            self.reaction_idx += 1
            self.window = (self.reactions[self.reaction_idx]['idx'], len(self.text))

        return reaction

    def evaluate_static_sentence_validity(self, text):
        text_list = text.split(' ')
        matching_sentences = {}
        # For all evaluated sentences, check if any of the words in it match to the given text. Then, find the position
        # where the match occurs, and get the length of the possible matching sentence.
        for i, s in enumerate(self.sentences):
            # Skip this sentence if it corresponds to the last match (it is unlikely that we process twice the same)
            if s['emotion'] == self.last_matched_emotion:
                continue
            first_match_id = None
            matched_sentence_length = 0
            sentence = s['sentence']
            for k, word in enumerate(sentence):
                if first_match_id is None:
                    for text_word in text_list:
                        if text_word == word:
                            first_match_id = text_list.index(text_word) - k
                            break
                else:
                    matched_sentence_length = min(len(text_list[first_match_id:]), len(sentence))
                    if matched_sentence_length / len(sentence) > self.match_score_thresh:
                        matching_sentences[i] = {'first_id': first_match_id, 'lenght': matched_sentence_length}
                    break
        # Once we have the matches, compare word by word the elements in the possible matches.
        best_score = self.match_score_thresh
        best_em = None
        for i in matching_sentences:
            recorded = text_list[matching_sentences[i]['first_id']:(matching_sentences[i]['first_id'] +
                                                                    matching_sentences[i]['lenght'])]
            template = self.sentences[i]['sentence'][0:matching_sentences[i]['lenght']]
            score = 0
            self.logger.debug('slen: {}\nrec: {}\ntem: {}'.format(matching_sentences[i]['lenght'], recorded, template))
            for rec, tem in zip(recorded, template):
                if rec == tem:
                    score += 1
            norm_score = score / len(self.sentences[i]['sentence'])
            if norm_score > best_score:
                best_score = norm_score
                best_em = self.sentences[i]['emotion']
                self.last_matched_emotion = best_em

        # Return the best matching emotion
        return best_em

    def evaluate_text(self, text):
        if self._in_expression_cooldown():
            return None

        expression = None
        bestmatch = 3
        global wordlist

        # Divide text into list of words, eliminate duplicates.
        text_filtered = []
        for w in text.split(' '):
            if w not in text_filtered:
                text_filtered.append(w)

        # Look for matches
        for em in wordlist:
            matches = 0
            for word in wordlist[em]:
                if word in text_filtered:
                    matches += 1
            if matches >= bestmatch:
                expression = em
                bestmatch = matches

        if expression is not None:
            self.last_expression_time = time.perf_counter()

        return expression

    def _in_expression_cooldown(self):
        return (time.perf_counter() - self.last_expression_time) < self.expression_cooldown

    @staticmethod
    def extract_keywords(text):
        """ Detect all unique words in the text. """
        all_keys = []
        for sentence in text:
            for word in sentence.split(' '):
                all_keys.append(word)

        # Find repeated keys
        repeats = []
        for i in range(len(all_keys)):
            for j in range(i + 1, len(all_keys)):
                if all_keys[j] == all_keys[i]:
                    repeats.append(all_keys[j])
        repeats = list(set(repeats))

        # Reasemble each line with all non-repeated keys. If a line contains only one element, pass
        filtered = []
        for i, sentence in enumerate(text):
            words = sentence.split(' ')
            if len(words) > 1 and '[' not in sentence:
                filtered.append(' '.join([w for w in words if w not in repeats]))
            else:
                filtered.append(sentence)

        return filtered
