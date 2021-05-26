"""
    Book reaction class.
"""

import logging
import re
import time
from typing import Dict, List, Optional

from .configuration_loader import resource_file, load_book


class NoMatchFound(Exception):
    """
        To mark when there is no matches.
    """
    pass


##
# Generation of list containing sentences that can be matched to specific emotions

# The teeny tree
sentencelist = {
    'happy':    ["pip saw a teeny green stem peeping out of the pot",
                 "keep them wet and wait"],

    'groan':    ["but for one very long week the pots just sat there",
                 "there was no tree to be seen",
                 "this is silly"],

    'excited':  ["yippee said Pip and Molly",
                 "and molly saw a soft green leaf",
                 "you have a tree said mr beam"],

    'sad':      ["molly was very sad",
                 "oh dear she said and a little tear fell down her cheek"],

    'scared':   ["and if we look X molly was screaming",
                 "three fat snails were sneaking along mr mister beams feet"]
}

# At the fun run
sentencelist['happy'] += ['at the end mum and I hug',
                          'we met my dad',
                          'we hug him too']
sentencelist['groan'] += ['the sun is hot',
                          'we get hot',
                          'I fan my mum']
sentencelist['excited'] += ['we run to the hut and on to the dam',
                            'we run on and on']
sentencelist['scared'] += ['I cut my leg',
                           'mum got the man']

# Mud
sentencelist['happy'] += ['we had buns and cans of pop yum',
                          'we dig it up and it hops on the bud']
sentencelist['groan'] += ['it can hop',
                          'it is not in my net']

# In the log hut
sentencelist['happy'] += ['the hut is set up',
                          'we had jam buns in it',
                          'the hut is fun']

# On the bus
sentencelist['happy'] += ['his dog had six pups',
                          'kaz and her pups nap in the box']
sentencelist['groan'] += ['she got on it',
                          'she can not sit']
sentencelist['scared'] += ['the man has his pet dog kaz on the bus',
                           'she is in her box']


# The big red box
sentencelist['happy'] += ['in the box is his sax and his wig for his job at the pub']
sentencelist['excited'] += ['dad is lots of fun']
sentencelist['scared'] += ['sam runs at the box',
                           'he rips at the lid']


class Book:
    """ Load and evaluate sentences from a book or sentencelist. """
    def __init__(self,
                 source: Optional[str] = 'the_teeny_tree_literal.txt',
                 sentences: Optional[Dict[List[str]]] = sentencelist) -> None:

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
                          for em in sentences for sen in sentences[em]]
        self.match_score_thresh = 0.5
        self.last_matched_emotion = None

    def evaluate_static_sentence_validity(self, text: str) -> str:
        """
            Compare a sentence with the reference emotion dict `self.sentences` and return the matched emotion if any.
        """

        text_list = text.split(' ')
        matching_sentences = {}
        # For all evaluated sentences, check if any of the words in it match to the given text. Then, find the position
        # where the match occurs, and get the length of the possible matching sentence.
        for i, s in enumerate(self.sentences):
            # Skip this sentence if it corresponds to the last match (it is unlikely that we process twice the same)
            if s['emotion'] == self.last_matched_emotion:
                continue

            try:
                match_loc = -1
                # Run until no match is found
                while True:
                    # 1. Find first word match
                    first_match_text, first_match_sentence, match_loc = self.find_match_start_point(text_list,
                                                                                                    s['sentence'],
                                                                                                    match_loc + 1)
                    # 2. Find last word match
                    matched_sentence_length = min(len(text_list[first_match_text:]),
                                                  len(s['sentence'][first_match_sentence:]))
                    if matched_sentence_length / len(s['sentence']) > self.match_score_thresh:
                        entry = {'first_id_text': first_match_text,
                                 'first_id_sentence': first_match_sentence,
                                 'lenght': matched_sentence_length}
                        matching_sentences[i] = matching_sentences[i] + [entry] if i in matching_sentences else [entry]
            except NoMatchFound:
                continue

        # Once we have the matches, compare word by word the elements in the possible matches.
        best_score = self.match_score_thresh
        best_em = None
        for i in matching_sentences:
            for entry in matching_sentences[i]:
                recorded = text_list[entry['first_id_text']:(entry['first_id_text'] + entry['lenght'])]
                template = self.sentences[i]['sentence'][entry['first_id_sentence']:(entry['first_id_sentence'] +
                                                                                     entry['lenght'])]
                score = 0
                self.logger.debug('slen: {}\nrec: {}\ntem: {}'.format(entry['lenght'], recorded, template))
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

    @staticmethod
    def extract_keywords(text: List[str]) -> List[str]:
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

    @staticmethod
    def find_match_start_point(rec, template, start_point=0):
        """ Find first match after `start_point."""
        for k in range(start_point, len(template)):
            word = template[k]
            for text_word in rec:
                if text_word == word:
                    if rec.index(text_word) - k >= 0:
                        first_idx_rec = rec.index(text_word) - k
                        first_idx_tem = 0
                    else:
                        first_idx_rec = 0
                        first_idx_tem = k - rec.index(text_word)
                    return (first_idx_rec, first_idx_tem, k)
        raise NoMatchFound
