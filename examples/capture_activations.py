# Copyright 2022 David Scripka. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

##################################

# This example scripts runs openWakeWord continuously on a microphone stream,
# and saves 5 seconds of audio immediately before the activation as WAV clips
# in the specified output location.

##################################

# Imports
import os
import platform
import collections
import time
if platform.system() == "Windows":
    import pyaudiowpatch as pyaudio
else:
    import pyaudio
import numpy as np
from openwakeword.model import Model
import scipy.io.wavfile
import datetime
import argparse

# Parse input arguments
parser=argparse.ArgumentParser()
parser.add_argument(
    "--output_dir",
    help="Where to save the audio that resulted in an activation",
    type=str,
    default="./",
    required=True
)
parser.add_argument(
    "--threshold",
    help="The score threshold for an activation",
    type=float,
    default=0.5,
    required=False
)
args=parser.parse_args()

# Get microphone stream
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1280
audio = pyaudio.PyAudio()
mic_stream = audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

# Load pre-trained openwakeword models
owwModel = Model()

# Set waiting period after activation before saving clip (to get some audio context after the activation)
save_delay = 1  # seconds

# Set cooldown period before another clip can be saved
cooldown = 4  # seconds

# Run capture loop, checking for hotwords
if __name__ == "__main__":
    # Predict continuously on audio stream
    last_save = time.time()
    activation_times = collections.defaultdict(list)

    print("\n\nListening for wakewords...\n")
    while True:
        # Get audio
        audio = np.frombuffer(mic_stream.read(CHUNK), dtype=np.int16)

        # Feed to openWakeWord model
        prediction = owwModel.predict(audio)

        # Check for model activations (score above threshold), and save clips
        for mdl in prediction.keys():
            if prediction[mdl] >= args.threshold:
                activation_times[mdl].append(time.time())

            if activation_times.get(mdl) and (time.time() - last_save) >= cooldown \
               and (time.time() - activation_times.get(mdl)[0]) >= save_delay:
                last_save = time.time()
                activation_times[mdl] = []
                detect_time = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
                print(f'Detected activation from \"{mdl}\" model at time {detect_time}!')

                audio_context = np.array(list(owwModel.preprocessor.raw_data_buffer)[-16000*5:]).astype(np.int16)
                fname = detect_time + f"_{mdl}.wav"
                scipy.io.wavfile.write(os.path.join(os.path.abspath(args.output_dir), fname), 16000, audio_context)