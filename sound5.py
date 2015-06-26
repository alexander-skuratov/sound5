import math
import struct
import pyaudio
import random
import time

NOTES = [261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00, 466.16, 493.88, 522]

#SEQ = [0,0,12,0,12,0,10,12,0,0,0,0,1,0,10,0,3,3,3,3,3,3,3,3,2,2,2,2,1,1,1,1]
SEQ  = [12,0,0,10,0,0,1,0,12,3,0,10,3,5,1,0,12,5,3,10,0,0,1,0,12,10,0,10,0,0,3,6]

offset_flag = True
offset = 1

class Core:
    fs = 48000
    ptr = 0
    output = 0
    noteContainer = []
    timebase_cnt = 0
    speed = 0
    
    def __init__(self):
        self.speed = int(0.1 * self.fs)
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.fs,
            output=True)
            
        self.stream.start_stream()
        self.run_loop()
        
        self.halt()
        
    def run_loop(self):
        while (True):
            self.clock()
            
            for _note in self.noteContainer:
                _chan = _note.get_sample()
                
                if (_chan == 'die'):
                    self.noteContainer.remove(_note)
                else: 
                    self.output =_chan * 0.05
            
            data = struct.pack('f', self.output)
            self.stream.write(data)
            
            self.ptr+=1
            
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
