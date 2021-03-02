"""
    Integration test for speech to text conversion.
"""

import argparse
import logging
import time
import subprocess
import os
from readingtorobot.common.continuous_speech import DEFAULT_SAMPLE_RATE
from readingtorobot.common.configuration_loader import load_config_file, resource_file
from readingtorobot.common.voice_recognition import SpeechReco


class SpeechRecoMock(SpeechReco):
    def __init__(self, config=None, interpreter=None):
        super().__init__(read_game=None, config=config, interpreter=interpreter)

    def process_text(self, text):
        self.logger.debug("\033[93mRecognized: {}\033[0m".format(text))
        op = self.book.evaluate_static_sentence_validity(text)
        if op is not None:
            self.logger.debug("\033[93mEvaluate text thinks: {}\033[0m".format(op))


def main():

    logging.basicConfig(format='%(asctime)s:SpeechTest:%(levelname)s:\033[32m%(name)s\033[0m: %(message)s',
                        level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="Stream from microphone to DeepSpeech using VAD")

    parser.add_argument('-v', '--vad_aggressiveness', type=int,
                        help="Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about"
                             "filtering out non-speech, 3 the most aggressive. Default: 3")
    parser.add_argument('-c', '--config',
                        help="Path to the configuration file.")
    parser.add_argument('-m', '--model',
                        help="Path to the model (protocol buffer binary file)")
    parser.add_argument('-s', '--scorer',
                        help="Path to the external scorer file.")
    parser.add_argument('-d', '--device', type=int, default=None,
                        help="Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not"
                        " provided, falls back to PyAudio.get_default_device().")
    parser.add_argument('-r', '--rate', type=int,
                        help=f"Input device sample rate. Default: {DEFAULT_SAMPLE_RATE}. Your device may require 44100."
                        )
    parser.add_argument('--hot_words', type=str,
                        help='Hot-words and their boosts.')

    parser.add_argument('--auto-play', action='store_true',
                        help="Plays automatically different audio samples on a loop. If not specified, the model will"
                             "just keep listening to any input.")

    parser.add_argument('-p', '--play', type=str, default=resource_file('the_teeny_tree_literal.txt'),
                        help="The audio to play on a loop, if not specified, the book will be read using espeak")

    args = parser.parse_args()

    # Load config parameters
    if args.config:
        configuration = load_config_file(args.config)
    else:
        configuration = {}

    # If given explicitly, override configuration parameters
    if args.model:
        configuration['model'] = args.model
    if args.scorer:
        configuration['scorer'] = args.scorer
    if args.vad_aggressiveness:
        configuration['vad_aggressiveness'] = args.vad_aggressiveness
    if args.rate:
        configuration['sample_rate'] = args.rate
    if args.device:
        configuration['device'] = args.device
    if args.hot_words:
        configuration['hot_words'] = {}
        for pair in args.hot_words.split(','):
            word, boost = pair.split(':')
            configuration['hot_words'][word] = boost

    # Create speech recognition object
    speech_reco = SpeechRecoMock(config=args.config)

    # Resource to play:
    reading_file = args.play

    try:
        speech_reco.start()
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common/play_text.sh")
        process = [script, reading_file]
        p = subprocess.Popen(process)
        while True:
            if p.poll() is not None:
                p = subprocess.Popen(process)
            time.sleep(1)
        speech_reco.join()

    except KeyboardInterrupt:
        speech_reco.stop()
        p.terminate()
        logging.info("Stopping, bye!")
        return


if __name__ == '__main__':
    main()
