"""
    Methods to manage audio recording.
"""

import collections
import io
import logging
import queue

import numpy as np
import pyaudio
import webrtcvad
import wave

from threading import Thread, Lock

from scipy import signal
from speech_recognition import AudioData

DEFAULT_SAMPLE_RATE = 16000


class Audio(object):
    """
        Streams raw audio from microphone.

        Data is received in a separate thread, and stored in a buffer.
    """

    FORMAT = pyaudio.paInt16
    # Network/VAD rate-space
    RATE_PROCESS = 16000
    CHANNELS = 1
    BLOCKS_PER_SECOND = 50

    def __init__(self, callback=None, device=None, input_rate=RATE_PROCESS, file=None, kwargs=None):
        def proxy_callback(in_data, frame_count, time_info, status):
            if self.chunk is not None:
                in_data = self.wf.readframes(self.chunk)
            callback(in_data)
            return (None, pyaudio.paContinue)
        if callback is None:
            def callback(in_data):
                self.buffer_queue.put(in_data)
        self.buffer_queue = queue.Queue()
        self.device = device
        self.input_rate = input_rate
        self.sample_rate = self.RATE_PROCESS
        self.block_size = int(self.RATE_PROCESS / float(self.BLOCKS_PER_SECOND))
        self.block_size_input = int(self.input_rate / float(self.BLOCKS_PER_SECOND))
        self.pa = pyaudio.PyAudio()

        kwargs = {
            'format': self.FORMAT,
            'channels': self.CHANNELS,
            'rate': self.input_rate,
            'input': True,
            'frames_per_buffer': self.block_size_input,
            'stream_callback': proxy_callback,
        }

        self.chunk = None
        # if not default device
        if self.device:
            kwargs['input_device_index'] = self.device
        elif file is not None:
            self.chunk = 320
            self.wf = wave.open(file, 'rb')

        self.stream = self.pa.open(**kwargs)
        self.stream.start_stream()

        self.logger = logging.getLogger(name=__name__)

    def resample(self, data, input_rate):
        """
        Microphone may not support our native processing sampling rate, so
        resample from input_rate to RATE_PROCESS here for webrtcvad
        Args:
            data (binary): Input audio stream
            input_rate (int): Input audio rate to resample from
        """
        data16 = np.frombuffer(data, dtype=np.int16)
        resample_size = int(len(data16) / self.input_rate * self.RATE_PROCESS)
        resample = signal.resample(data16, resample_size)
        resample16 = np.array(resample, dtype=np.int16)
        return resample16.tobytes()

    def read_resampled(self):
        """Return a block of audio data resampled to 16000hz, blocking if necessary."""
        return self.resample(data=self.buffer_queue.get(),
                             input_rate=self.input_rate)

    def read(self):
        """Return a block of audio data, blocking if necessary."""
        return self.buffer_queue.get()

    def destroy(self):
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

    frame_duration_ms = property(lambda self: 1000 * self.block_size // self.sample_rate)

    def write_wav(self, filename, data):
        logging.info("write wav %s", filename)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(self.CHANNELS)
        # wf.setsampwidth(self.pa.get_sample_size(FORMAT))
        assert self.FORMAT == pyaudio.paInt16
        wf.setsampwidth(2)
        wf.setframerate(self.sample_rate)
        wf.writeframes(data)
        wf.close()


class ContinuousSpeech(Thread, Audio):
    """
        Get and process audio streams continuously.

        To do this, a thread keeps storing audio in a buffer of size 1 to 5s.
        Meanwhile, the model processes a previous buffer. Once the processing is done, we swap buffers.
    """

    def __init__(self,
                 device=None,
                 max_seconds=10,
                 min_seconds=4,
                 aggressiveness=3,
                 processing_interval=0.5,
                 silence_threshold=200,
                 input_rate=None):
        super().__init__()
        super(Thread, self).__init__(device=device, input_rate=input_rate)
        self.vad = webrtcvad.Vad(aggressiveness)
        self.lock = Lock()
        self.max_seconds = max_seconds
        self.min_seconds = min_seconds
        self.time_window = (max_seconds - min_seconds) * self.BLOCKS_PER_SECOND
        self.wait_time = processing_interval
        self.main_buffer_size = self.BLOCKS_PER_SECOND * self.max_seconds

        self.main_audio_buffer = []
        self.running = False
        self.unvoiced_threshold = silence_threshold

    def start(self):
        self.running = True
        super().start()

    def stop(self):
        self.running = False
        self.join()

    def frame_generator(self):
        """Generator that yields all audio frames from microphone."""
        if self.input_rate == self.RATE_PROCESS:
            while self.running:
                yield self.read()
        else:
            while self.running:
                yield self.read_resampled()

    def run(self):
        """Function storing audio buffers."""
        while self.running:
            triggered = False
            num_unvoiced = 0
            for frame in self.frame_generator():
                # Check for speech around the robot. If there is speech, increase the translation rate.
                if not self.vad.is_speech(frame, self.sample_rate):
                    if triggered:
                        num_unvoiced += 1
                        if num_unvoiced > self.unvoiced_threshold:
                            with self.lock:
                                del self.main_audio_buffer[:]
                            triggered = False
                            num_unvoiced = 0
                    continue

                triggered = True
                # Put a new element in buffer.
                with self.lock:
                    # If buffer is full, extract audio of the first n seconds until buffer size is the minimum again
                    if len(self.main_audio_buffer) > self.main_buffer_size:
                        del self.main_audio_buffer[self.time_window:]
                    self.main_audio_buffer.insert(0, frame)

    def get_audio(self, time_diff=0):
        """ Clears part of the time buffer corresponding to the elapsed time (time_diff (seconds)), leaving at least the
            minimum size. """

        output = None
        to_clear = int(self.BLOCKS_PER_SECOND * max(0, (len(self.main_audio_buffer)/self.BLOCKS_PER_SECOND -
                                                        self.min_seconds - time_diff)))
        self.logger.debug('Clearing: {}, of a total of {}'
                          .format(to_clear, len(self.main_audio_buffer)))

        with self.lock:
            output = self.main_audio_buffer
            if to_clear:
                del self.main_audio_buffer[-to_clear:]

        return reversed(output)

    def frames_to_SR(self, frames):
        """ Convert frames into an AudioData object (to use with Speech Recognition). """
        byte_frames = io.BytesIO()
        for frame in frames:
            byte_frames.write(frame)
        frame_data = byte_frames.getvalue()
        byte_frames.close()
        return AudioData(frame_data, self.sample_rate, 2)

    def clear_audio(self, clear_all=False):
        """ Clean up the current window. """
        with self.lock:
            if clear_all:
                del self.main_audio_buffer[:]
            else:
                del self.main_audio_buffer[self.time_window:]

    def vad_collector(self, padding_ms=300, ratio=0.75, frames=None):
        """ Generator that yields series of consecutive audio frames comprising each utterence, separated by yielding a
            single None. Determines voice activity by ratio of frames in padding_ms. Uses a buffer to include padding_ms
            prior to being triggered.
            Example: (frame, ..., frame, None, frame, ..., frame, None, ...)
                      |---utterence---|        |---utterence---|
        """
        if frames is None:
            frames = self.frame_generator()
        num_padding_frames = padding_ms // self.frame_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False

        for frame in frames:
            if len(frame) < 640:
                return

            is_speech = self.vad.is_speech(frame, self.sample_rate)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > ratio * ring_buffer.maxlen:
                    triggered = True
                    for f, s in ring_buffer:
                        yield f
                    ring_buffer.clear()

            else:
                yield frame
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > ratio * ring_buffer.maxlen:
                    triggered = False
                    yield None
                    ring_buffer.clear()

    @classmethod
    def from_json(cls, data):
        return ContinuousSpeech(max_seconds=data.get('max_seconds', 10),
                                min_seconds=data.get('min_seconds', 4),
                                aggressiveness=data.get('vad_aggressiveness', 3),
                                silence_threshold=data.get('silence_threshold', 200),
                                device=data.get('device', None),
                                processing_interval=data.get('processing_interval', 0.5),
                                input_rate=data.get('sample_rate', DEFAULT_SAMPLE_RATE))
