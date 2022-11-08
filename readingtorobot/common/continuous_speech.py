"""Methods to manage audio recording."""

import collections
import io
import logging
import queue
from typing import BinaryIO, ByteString, Callable, Optional

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
    frame_duration_ms = property(lambda self: 1000 * self.block_size // self.sample_rate)

    def __init__(
        self,
        callback: Optional[Callable] = None,
        device: Optional[int] = None,
        input_rate: int = RATE_PROCESS,
        file: Optional[str] = None,
    ):
        """Initialize Audio.

        :param callback: Callback executed when a sentence is detected.
        :param device: The recording device (index) to use.
        :param input_rate: Recording sampling rate.
        :param file: File to write the recorded audio.
        """

        def proxy_callback(in_data, frame_count, time_info, status):
            del frame_count, time_info, status
            if self._chunk is not None:
                in_data = self._wf.readframes(self._chunk)
            self.callback(in_data)
            return (None, pyaudio.paContinue)

        if callback is None:

            def default_callback(in_data):
                self._buffer_queue.put(in_data)

            self.callback = default_callback
        else:
            self.callback = callback

        self._buffer_queue = queue.Queue()
        self._input_rate = input_rate
        self._sample_rate = self.RATE_PROCESS
        self._block_size = int(self.RATE_PROCESS / float(self.BLOCKS_PER_SECOND))
        self._block_size_input = int(self._input_rate / float(self.BLOCKS_PER_SECOND))
        self._pa = pyaudio.PyAudio()

        kwargs = {
            "format": self.FORMAT,
            "channels": self.CHANNELS,
            "rate": self._input_rate,
            "input": True,
            "frames_per_buffer": self._block_size_input,
            "stream_callback": proxy_callback,
        }

        self._chunk = None
        # if not default device
        if device:
            kwargs["input_device_index"] = device
        elif file is not None:
            self._chunk = 320
            self._wf = wave.open(file, "rb")

        self._stream = self._pa.open(**kwargs)
        self._stream.start_stream()

        self._logger = logging.getLogger(name=__name__)

    def _resample(self, data: bytes, input_rate: int):
        """
        Resample from input_rate to RATE_PROCESS for webrtcvad.

        Microphone may not support our native processing sampling rate.

        :param data: Input audio stream
        :param input_rate: Input audio rate to resample from
        """
        data16 = np.frombuffer(data, dtype=np.int16)
        resample_size = int(len(data16) / input_rate * self.RATE_PROCESS)
        resample = signal.resample(data16, resample_size)
        resample16 = np.array(resample, dtype=np.int16)
        return resample16.tobytes()

    def _read_resampled(self):
        """Return a block of audio data resampled to 16000hz, blocking if necessary."""
        return self._resample(data=self._buffer_queue.get(), input_rate=self._input_rate)

    def _read(self):
        """Return a block of audio data, blocking if necessary."""
        return self._buffer_queue.get()

    def stop(self):
        """Stop audio stream."""
        self._stream.stop_stream()
        self._stream.close()
        self._pa.terminate()

    def write_wav(self, filename: str, data: bytes):
        """Write recorded audio to provided data file."""
        logging.info("write wav %s", filename)
        wf = wave.open(filename, "wb")
        wf.setnchannels(self.CHANNELS)
        # wf.setsampwidth(self.pa.get_sample_size(FORMAT))
        assert self.FORMAT == pyaudio.paInt16
        wf.setsampwidth(2)
        wf.setframerate(self._sample_rate)
        wf.writeframes(data)
        wf.close()


class ContinuousSpeech(Thread, Audio):
    """
    Get and process audio streams continuously.

    To do this, a thread keeps storing audio in a buffer of size 1 to 5s.
    Meanwhile, the model processes a previous buffer. Once the processing is done, we swap buffers.
    """

    def __init__(
        self,
        device=None,
        max_seconds=10,
        min_seconds=4,
        aggressiveness=3,
        processing_interval=0.5,
        silence_threshold=200,
        input_rate=None,
    ):
        """Initialize ContinuousSpeech."""
        super().__init__()
        super(Audio, self).__init__(device=device, input_rate=input_rate)
        self._vad = webrtcvad.Vad(aggressiveness)
        self._lock = Lock()
        self._min_seconds = min_seconds
        self._time_window = (max_seconds - min_seconds) * self.BLOCKS_PER_SECOND
        self.wait_time = processing_interval
        self._main_buffer_size = self.BLOCKS_PER_SECOND * max_seconds

        self._main_audio_buffer = []
        self._running = False
        self._unvoiced_threshold = silence_threshold

    def start(self):
        """Start thread."""
        self._running = True
        super().start()

    def stop(self):
        """Stop thread."""
        self._running = False
        self.join()

    def _frame_generator(self):
        """Yield all audio frames from microphone."""
        if self._input_rate == self.RATE_PROCESS:
            while self._running:
                yield self._read()
        else:
            while self._running:
                yield self._read_resampled()

    def run(self):
        """Manage audio buffers."""
        while self._running:
            triggered = False
            num_unvoiced = 0
            for frame in self._frame_generator():
                # Check for speech around the robot. If there is speech, increase the translation rate.
                if not self._vad.is_speech(frame, self._sample_rate):
                    if triggered:
                        num_unvoiced += 1
                        if num_unvoiced > self._unvoiced_threshold:
                            with self._lock:
                                del self._main_audio_buffer[:]
                            triggered = False
                            num_unvoiced = 0
                    continue

                triggered = True
                # Put a new element in buffer.
                with self._lock:
                    # If buffer is full, extract audio of the first n seconds until buffer size is the minimum again
                    if len(self._main_audio_buffer) > self._main_buffer_size:
                        del self._main_audio_buffer[self._time_window :]
                    self._main_audio_buffer.insert(0, frame)

    def get_audio(self, time_diff: int = 0):
        """Clear part of the time buffer corresponding to the elapsed time (time_diff (seconds))."""
        output = None
        to_clear = int(
            self.BLOCKS_PER_SECOND
            * max(0, (len(self._main_audio_buffer) / self.BLOCKS_PER_SECOND - self._min_seconds - time_diff))
        )
        self._logger.debug("Clearing: {}, of a total of {}".format(to_clear, len(self._main_audio_buffer)))

        with self._lock:
            output = self._main_audio_buffer
            if to_clear:
                del self._main_audio_buffer[-to_clear:]

        return reversed(output)

    def frames_to_SR(self, frames):
        """Convert frames into an AudioData object (to use with Speech Recognition)."""
        byte_frames = io.BytesIO()
        for frame in frames:
            byte_frames.write(frame)
        frame_data = byte_frames.getvalue()
        byte_frames.close()
        return AudioData(frame_data, self._sample_rate, 2)

    def clear_audio(self, clear_all=False):
        """Clean up the current window."""
        with self._lock:
            if clear_all:
                del self._main_audio_buffer[:]
            else:
                del self._main_audio_buffer[self._time_window :]

    def _vad_collector(self, padding_ms=300, ratio=0.75, frames=None):
        """Yield a series of consecutive audio frames comprising each utterence.

        Each utterence is separated with a single None. Determines voice activity by ratio of frames in padding_ms.
        Uses a buffer to include padding_ms prior to being triggered.
        Example: (frame, ..., frame, None, frame, ..., frame, None, ...)
                  |---utterence---|        |---utterence---|
        """
        if frames is None:
            frames = self._frame_generator()
        num_padding_frames = padding_ms // self.frame_duration_ms
        ring_buffer = collections.deque(maxlen=num_padding_frames)
        triggered = False

        for frame in frames:
            if len(frame) < 640:
                return

            is_speech = self._vad.is_speech(frame, self._sample_rate)

            if not triggered:
                ring_buffer.append((frame, is_speech))
                num_voiced = len([f for f, speech in ring_buffer if speech])
                if num_voiced > ratio * (ring_buffer.maxlen or 0):
                    triggered = True
                    for f, _ in ring_buffer:
                        yield f
                    ring_buffer.clear()

            else:
                yield frame
                ring_buffer.append((frame, is_speech))
                num_unvoiced = len([f for f, speech in ring_buffer if not speech])
                if num_unvoiced > ratio * (ring_buffer.maxlen or 0):
                    triggered = False
                    yield None
                    ring_buffer.clear()

    @classmethod
    def from_json(cls, data):
        """Initialize using JSON description."""
        return ContinuousSpeech(
            max_seconds=data.get("max_seconds", 10),
            min_seconds=data.get("min_seconds", 4),
            aggressiveness=data.get("vad_aggressiveness", 3),
            silence_threshold=data.get("silence_threshold", 200),
            device=data.get("device", None),
            processing_interval=data.get("processing_interval", 0.5),
            input_rate=data.get("sample_rate", DEFAULT_SAMPLE_RATE),
        )
