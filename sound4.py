"""
FM synthesis example
Don't have enough time to comment, look @ sound5.py 
"""

import math
import struct
import pyaudio
import random
notes = [261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 522]
seq = [0,4,2,5,4,7,5,9,7,11]

fs = 48000

def play_sample(_float):
    data = struct.pack('f', _float)
    stream.write(data)
fs = 48000
p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paFloat32,
    channels=1,
    rate=fs,
    output=True)

i = 1

class SineGen:
    s0 = 0.5
    s1 = 0
    
    def __init__(self):
        pass
    
    def play(self, freq):
        a = 2 * math.sin(3.14159*freq/fs)
        self.s0 = self.s0 - a * self.s1
        self.s1 = self.s1 + a * self.s0
        return self.s1

sine = SineGen()
sine4 = SineGen()
sine2 = SineGen()
lfo = SineGen()

note_ptr = 0
note_ptr_prev = 0
env_ptr = 0
env = 1
fall = False
risespeed = int(0.005 * fs)
fallspeed = int(0.2 * fs)
while (True):
    """ Frequency vibrato """
    note = notes[note_ptr] * 0.25 + (5 * lfo.play(10))
    
    """ FM Syntesis """
    freq = note * ((sine2.play(note * 2) + 1.1) * 1.4) * ((sine2.play(note * 3) + 1) * 1.5 + (sine4.play(note * 5) * 1.3))
    a = sine.play(freq)

    a = a* 2
    play_sample(a*env)
    i = i+1
    env_ptr = env_ptr+1
    if not (fall):
        env = env_ptr / float(risespeed)
        if (env_ptr % risespeed == 0):
            env_ptr = 0
            fall = True
    else: 
        env = 1.0 - (env_ptr / float(fallspeed))
        if (env_ptr % fallspeed == 0):
            env_ptr = 0
            fall = False
    
    
    if (i % (risespeed + fallspeed) == 0): 
        note_ptr_prev = note_ptr
        while (note_ptr == note_ptr_prev):
            
            note_ptr = random.randint(0,12)
        
            print str(note) + " Hz"

    if (note_ptr == len(seq)): note_ptr = 0


stream.close()
p.terminate()
