import logging
import unittest
from readingtorobot.common.book_reactions import Book

sentencelist = {
    'happy': ["then one happy day in the second week",
              "keep them wet and wait"],

    'groan': ["but for one very long week the pots just sat there",
              "there was no tree to be seen",
              "this is silly"],

    'excited': ["pip saw a teeny green stem peeping out of the pot",
                "and molly saw a soft green leaf",
                "you have a tree said mr beam"],

    'sad': ["but the next day the teeny green stem and the soft green leaf had vanished",
            "molly was very sad",
            "oh dear she said and a little tear fell down her cheek"],

    'scared': ["three fat snails were sneaking along mr mister beams feet"]
}


class BookTests(unittest.TestCase):

    def test_evaluate_static_sentence_validity(self):
        book = Book()

        tests = [  # No matching
                 {'text': 'some text',
                  'res': None},
                 {'text': 'some text with many words but no matches',
                  'res': None},
                 {'text': 'some text with only matching but the next day',
                  'res': None},
                 {'text': 'but the next day is the matching text',
                  'res': None},
                 {'text': 'the text but the next day is matching',
                  'res': None},
                 # Matching
                 {'text': 'this is silly',
                  'res': 'groan'},
                 {'text': 'blah blah this is silly',
                  'res': 'groan'},
                 {'text': 'this is silly blah blah',
                  'res': 'groan'},
                 {'text': 'some this is silly text',
                  'res': 'groan'},
                 {'text': 'some more and more this is silly blah text',
                  'res': 'groan'},
                 {'text': 'some more and more this blah silly blah text',
                  'res': 'groan'}
                  ]

        for test in tests:
            res = book.evaluate_static_sentence_validity(test['text'])
            self.assertEqual(res, test['res'])


if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s:SpeechTest:%(levelname)s:\033[32m%(name)s\033[0m: %(message)s',
                        level=logging.DEBUG)
    unittest.main()
