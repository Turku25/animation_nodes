from . MIDINote import MIDINote
#from MIDINote import MIDINote
class MIDITrack():
    def __init__( self ):
        self.noteData = [ [] for i in range(0, 128)]
    
    def __repr__(self):
        return self.noteData.__repr__()
        
    def copy(self):
        m = MIDITrack()
        for row in range(0, len ( self.noteData )):
            for note in self.noteData[row]:
                m.noteData[row].append(note)
        return m
    
    def clear(self):
        for noteCol in self.noteData:
            noteCol.clear()
     
    def hasNotes(self):
        for i in range(0, len( self.noteData )):
            if len( self.noteData[i] ) > 0:
                return True
        return False
    #def noteCount(self):
    #    count = 0
    #    for i in range(0, len( self.noteData )):
    #        count += len( self.noteData[i] )
    #    return count
            
    def clearFinishedNotes(self):
        for noteCol in self.noteData:
            for NOTE in noteCol:
                if not NOTE.duration == -1:
                    noteCol.remove(NOTE)
    
    
    #def timeTrim(self, min, max):#milis since beginning                
    #    for noteCol in self.noteData:
    #        for note in noteCol:
    #            if not note.duration == -1:  #DONT TRIM IF NOTE STILL IN PROGRESS
    #                if note.startTime < min:
    #                    noteCol.remove(note)
    #                    continue
    #                if note.starTIme > max:
    #                    noteCol.remove(note)
                        
    def trimSmall(self, min):
        for noteCol in self.noteData:
            heldNotes = []
            noteCol.reverse()
            while True:# for ind in range(0, len( noteCol )):
                if len( noteCol ) <= 0:# there are no notes left to pop
                    break
                note = noteCol.pop()
                if note.startTime >= min:
                    noteCol.append(note)#this will be in the same spot if appended to either noteCol or heldNotes, but this way should be easier on the reverse method
                    break
                #print("removed small note: %s   start %s    duration %s     min %s"%(note.note, note.startTime, note.duration, min))
                if note.duration == -1 or note.startTime + note.duration >= min:  #DONT TRIM IF NOTE STILL IN PROGRESS
                    heldNotes.append(note)
                    #print("note %s was re-appended"%note.note)
            heldNotes.reverse()
            noteCol.extend(heldNotes)
            noteCol.reverse()
                    
    def trimBig(self, max):
        for noteCol in self.noteData:
            #if len( noteCol ) > 0:
            for i in range(0, len( noteCol ) ):#while temp.startTime >= max:
                temp = noteCol.pop()
                #print("trim big just popped note %s"%temp.note)
                if temp.startTime < max:
                    noteCol.append(temp)
                    #print("jk, that last one got pushed back on.")
                    break
                
                
                    
    def noteOn(self, note, vel, time, channel):
        n = MIDINote(note, vel, time, channel)#create note
        #print("at time %s I tried to play note %s"%(time, note))
        if len( self.noteData[note] ) > 0:
            prev = self.noteData[note].pop()
            self.noteData[note].append(prev)
            if prev.duration == -1:
                self.noteOff(note, vel, time, channel)
                print("I had to manually cancel a note, this might be a problem..")
        #print("A note was appended . it should be ok. note %s"%note)
        self.noteData[note].append(n)#add to proper location
        
      
    def noteOff(self, note, vel, time, channel):#there sould only be one note open at a time so why am I even treating it like a stack????
        end = len(self.noteData[note]) - 1#top of stack?
        #print("size of stack for note %s is %s"%(note, len(self.noteData[note]))
        if end < 0:
            print("what the hell, this should never happen. note %s"%note)#self.noteOn(note, vel, -1)
            #end += 1
        else:
            prevchan = self.noteData[note].pop()
            self.noteData[note].append(prevchan)
            if not prevchan.channel == channel:
                print("channel missmatch error. first was %s, the second was %s"%(prevchan.channel, channel))
            if self.noteData[note][end].duration == -1:
                self.noteData[note][end].endNote(time, channel)
            else:#just for debug
                print("tried to close an already closed note dummy...")