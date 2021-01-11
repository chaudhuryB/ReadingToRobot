"""
    Integration test for speech to text conversion.
"""

import time
import subprocess
import os
from ..common.deepspeech_module import DEFAULT_SAMPLE_RATE
from ..common.configuration_loader import load_config_file
from ..common.voice_recognition import SpeechReco


class SpeechRecoMock(SpeechReco):
    def __init__(self, config=None, interpreter=None):
        super().__init__(read_game=None, config=config, interpreter=interpreter)

    @staticmethod
    def emotion_from_string(text):
        print("\033[93mRecognized: {}\033[0m".format(text))


def main():

    import argparse
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

    try:
        speech_reco.start()
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "common/play_text.sh")
        process = [script, "Pip saw a teeny green stem peeping out of the pot"]
        p = subprocess.Popen(process)
        while True:
            if p.poll() is not None:
                p = subprocess.Popen(process)
            time.sleep(1)
        speech_reco.join()

    except KeyboardInterrupt:
        speech_reco.stop()
        p.terminate()
        print("Stopping, bye!")
        return


if __name__ == '__main__':
    main()
