"""
    Load deepspeech model.
"""

import logging
import os

import deepspeech


def load_deepspeech_model(configuration: dict) -> deepspeech.Model:
    """ Initialize a deepspeech model with a specific configuration. """
    ds = None
    if 'model' in configuration:
        path = configuration['model'].format(DEEPSPEECH_DIR=os.getenv('DEEPSPEECH_DIR', default='.'))
        logging.info("model: %s", path)
        ds = deepspeech.Model(path)
    else:
        logging.error("Please provide model via Config file or model address.")
        raise Exception("No detection model provided.")

    if 'scorer' in configuration:
        path = configuration['scorer'].format(DEEPSPEECH_DIR=os.getenv('DEEPSPEECH_DIR', '.'))
        logging.info("scorer: %s", path)
    else:
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "resources/kenlm.scorer")
        logging.info("scorer: %s", path)

    ds.enableExternalScorer(path)

    if 'hot_words' in configuration:
        logging.info('Adding hot-words %s', configuration['hot_words'])
        for word in configuration['hot_words']:
            ds.addHotWord(word, float(configuration['hot_words'][word]))
    return ds
