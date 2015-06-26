"""
Caution:

1) Low performance
2) Envelopes are not stable and linear (better use exp. interpolation or any other - it's smoother)
3) Filter are not so stable

So if you tweak the parameters you can get some unexceptable results (that may be very loud)
"""

import math
import struct
import pyaudio


"""
Notes frequencies from C4 to C5
"""
NOTES = [261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 522]

"""
Note sequence (0 is C4, 1 is C#4, etc...)
"""
SEQ  = [12,0,0,10,0,0,1,0,12,3,0,10,3,5,1,0,12,5,3,10,0,0,1,0,12,10,0,10,0,0,3,6]

"""
Some rude global vars for transposition
"""
offset_flag = True 
offset = 1

"""
Core class with bootstrapping, etc...
"""

class Core:
    fs = 48000 # samplerate (48000 Hz in our case)
    ptr = 0 # pointer which continiously increases on every tick
    output = 0 #float audio sample value
    noteContainer = []
    timebase_cnt = 0 #note counter
    speed = 0 #init speed
    
    """
    Bootstrap routine
    """
    
    def __init__(self):
        self.speed = int(0.1 * self.fs)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.fs,
            output=True)
            
        self.stream.start_stream()
        self.run_loop() #Here we can call the main routine
        
        self.halt()
        
    def run_loop(self):
        """
        One iteration of that loop = 1 tick
        """
        while (True):
            self.clock() # "Sequencer" subroutine
            
            for _note in self.noteContainer:
                _chan = _note.get_sample() # Asking every note for a sample float
                
                if (_chan == 'die'):
                    self.noteContainer.remove(_note) # #Kill notes which finished playing
                else: 
                    self.output =_chan * 0.05 #Make it not so loud
            
            data = struct.pack('f', self.output) #PyAudio packing float into binary string
            self.stream.write(data) #After that point the soundcard playing the sound
            
            self.ptr+=1 #Global pointer (dunno deprecated or not)
   
    """
    "Sequencer" for the demo purposes
    """
            
    def clock(self):
        global offset
        global offset_flag
        if (self.ptr % self.speed == 0): #tick
            self.noteContainer.append(Note((NOTES[SEQ[self.timebase_cnt]]*offset), 0.002, 0.1))
            self.timebase_cnt+=1
            if (self.timebase_cnt == 32): 
                self.timebase_cnt = 0
                
                if (offset_flag): 
                    offset = 1
                    offset_flag = False
                    print 'TRANSPOSE 0'
                else:
                    print 'TRANSPOSE +5 SEMITONES'
                    offset = 1.333
                    offset_flag = True
            
    def halt(self):
        self.stream.close()
        self.p.terminate()
"""Sinewave Generator (C->Python port from MusicDsp.Org)"""        
class SineGen(Core):
    s0 = 0.5
    s1 = 0
    _a = 0
    
    def __init__(self, freq):
        self._a = 2 * math.sin(3.14159*freq/self.fs)
    
    def play(self):
        
        self.s0 = self.s0 - self._a * self.s1
        self.s1 = self.s1 + self._a * self.s0
        return self.s0

"""Squarewave Generator (not band-limited, just switching -1 and 1)"""        
class SquareGen(Core):
    sign = 1
    freq = 0
    
    def __init__(self, freq):
	    self.freq = freq
	    self.sign = 1
    
    def play(self):
        if (self.ptr % math.floor(2.0 * self.fs / self.freq) == 0):
            self.sign *= -1
        self.ptr +=1
        return self.sign
          
class Note(Core):
    sine = {}
    freq = 440
    note_ptr = 0
    _ptr = 0
    rise = 1
    fall = 1
    _fall = False
    f_input = [0,0,0,0]
    f_output = [0,0,0,0]
    
    def __init__(self, freq, rise, fall):
        #self.generator = SineGen(freq)
        self.generator = SquareGen(freq)
        self.generator2 = SquareGen(freq * 2.02)
        self.generator3 = SquareGen(freq * 3.95)
        self.rise = int(rise * self.fs)
        self.fall = int(fall * self.fs)
        self.note_ptr = 0
        self.lfo = SineGen(1)
        
    """ Sample getter + very basic and rude LERP Envelope Generator"""    
    def get_sample(self):
        if not (self._fall):
            env = self.note_ptr / float(self.rise)
            if (self.note_ptr == self.rise):
                    self.note_ptr = 0
                    self._fall = True
        else: 
            env = 1.0 - (self.note_ptr / float(self.fall))
            if (self.note_ptr % self.fall == 0):
                self.note_ptr = 1
                self._fall = False
                return 'die'
                
        self.note_ptr+=1
        self._ptr+=1
        
        a = (self.generator.play()*2) + self.generator2.play() + self.generator3.play() * env
        
        a = self.filter(a, 0.1 + (env / 5), 1)

        return a * 20
        
    """Moog 24dB/OCT ladder filter (C->Python port from MusicDsp.Org)
    A = float input signal (min -1 max 1)
    fc = cutoff frequency (min 0 max self.fs / 2)
    res = resonance level (min 0 max 4)
    
    """ 
        
    def filter(self, a, fc, res):
        f = fc * 1.16;
        fb = res * (1.0 - 0.15 * f * f);
        a -= self.f_output[3] * fb;
        a *= 0.35013 * (f*f)*(f*f);
        self.f_output[0] = a + 0.3 * self.f_input[0] + (1 - f) * self.f_output[0];
        self.f_input[0]  = a;
        self.f_output[1] = self.f_output[0] + 0.3 * self.f_input[1] + (1 - f) * self.f_output[1];
        self.f_input[1]  = self.f_output[0];
        self.f_output[2] = self.f_output[1] + 0.3 * self.f_input[2] + (1 - f) * self.f_output[2];
        self.f_input[2]  = self.f_input[1];
        self.f_output[3] = self.f_output[2] + 0.3 * self.f_input[3] + (1 - f) * self.f_output[3];
        self.f_input[3]  = self.f_output[2];
        return self.f_output[3];
   

core = Core()
