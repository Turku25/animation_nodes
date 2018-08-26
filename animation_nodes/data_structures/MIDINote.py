class MIDINote(object):
    def __init__( self, noteValue, velocity, start, channel, duration = -1 ):
        self.note = noteValue
        self.startTime = start
        self.duration = duration
        self.vel = velocity
        self.channel = channel
        
    def endNote(self, time, channel):
        self.duration = time - self.startTime
        
    def copy(self):
        return MIDINote(self.note, self.vel, self.startTime, self.channel, self.duration)