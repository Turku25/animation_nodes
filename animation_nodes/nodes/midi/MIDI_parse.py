import sys

import bpy
from ... data_structures.MIDITrack import MIDITrack
from ... base_types.node import AnimationNode
#import sys

#import bpy
#from ... data_structures import MIDITrack
#from ... base_types.node import AnimationNode
#from MIDITrack import MIDITrack



def VLQUnpack32(f):
    quant = 0
    count = 1
    by = f.read(1)
    byte = int.from_bytes(by, byteorder='big')
    size = sys.getsizeof(byte)
    while 128 & byte == 128:
        quant = quant << 7
        quant = (quant | (byte & 127))
        by = f.read(1)
        byte = int.from_bytes(by, byteorder='big')
        count += 1
    quant = quant << 7
    quant = (quant | (byte & 127))
    return quant, count
    
def readChunkHeader(f):
    
    IDBytes = f.read(4)
    lengthBytes = f.read(4)
    ID = IDBytes.decode('ascii')
    length = int.from_bytes(lengthBytes, byteorder='big')
    #print("Read headder for chunk %s" % ID)
    return (ID, length)
          
def readMThdChunk(f):
    formatBytes = f.read(2)
    MTrkBytes = f.read(2)
    timeBytes = f.read(2)
    ppqn = 0
    Dtime = 0
    format = int.from_bytes(formatBytes, byteorder='big')
    MTrk = int.from_bytes(MTrkBytes, byteorder='big')
    print("number of MtTrks is %s" % MTrk)
    if (timeBytes[0] & b'\x80'[0]) == b'\x80'[0]:
        frame = int.from_bytes(timeBytes[0], byteorder='big', signed=True)
        division = int.from_bytes(timeBytes[1], byteorder='big')
        Dtime = frame * division
    else:
        ppqn = int.from_bytes(timeBytes, byteorder='big')
    return format, MTrk, ppqn, Dtime  

    
def miliToPulse(ppqn, tempo, Dtime, milis):#check this data for validity during read file
    
    if ppqn == 0:                               
        return ( Dtime * milis ) / 1000        
        
    else:                                          
        return (milis * 1000 * ppqn ) / tempo            

def pulseToMili(ppqn, tempo, Dtime, pulses):  
    if ppqn == 0:
        return ( pulses * 1000 ) / Dtime
    else:
        return ( pulses * tempo ) / ( ppqn * 1000)
        
        
    
######################     NODE CLASS     ###############################   add file validity check
class MIDIParseNode(bpy.types.Node, AnimationNode):
    bl_idname = "MIDIParse"
    bl_label = "MIDI Parser"

    MIDIFile = None
    format = 0
    ppqn = 0
    division = 0
    oldPath = ""
    dataTrack = None
    trackReaderList = []
    trackList = []
    oldStart = 0
    oldEnd = 0
    validFile = False
        
        
        
    def newFileSetup(self, filePath):
        if not MIDIParseNode.MIDIFile == None:
            MIDIParseNode.MIDIFile.close()#close out old file (what if it's null?)
        #MIDIParseNode.validFile = False
        MIDIParseNode.format = 0
        MIDIParseNode.ppqn = 0
        MIDIParseNode.division = 0
        MIDIParseNode.dataTrack = None
        MIDIParseNode.trackReaderList = []
        MIDIParseNode.trackList = []
        MIDIParseNode.oldStart = 0
        MIDIParseNode.oldEnd = 0
        MIDIParseNode.MIDIFile = open(filePath, "rb")#open the new one
        chunkID, mthdSize = readChunkHeader(MIDIParseNode.MIDIFile)
        if chunkID == "MThd":
            MIDIParseNode.format, tracks, MIDIParseNode.ppqn, MIDIParseNode.division = readMThdChunk(MIDIParseNode.MIDIFile)
            
            byteLoc = 14#start of first MTrk is a constant of 14
            print("about to search for %s tracks" % tracks)
            for track in range(0, tracks):
                ID, size = readChunkHeader(MIDIParseNode.MIDIFile)#read header and length
                byteLoc += 8
                if ID == "MTrk":
                    if MIDIParseNode.format == 1 and track == 0:
                        print("setting up tempo map")
                        MIDIParseNode.dataTrack = TempoMapReader(MIDIParseNode.MIDIFile, byteLoc, size, MIDIParseNode.ppqn, MIDIParseNode.division)#(self, f, start, size, ppqn, Dtime):
                        print("map reader set up. ready to seek.")
                        MIDIParseNode.MIDIFile.seek(MIDIParseNode.dataTrack.trackStart )
                        print("finnished tempo map")
                    else:
                        print("building new mtrk")
                        newNoteReader = NoteReader(MIDIParseNode.MIDIFile, byteLoc, size, MIDIParseNode.ppqn, MIDIParseNode.division)
                        MIDIParseNode.trackReaderList.append( newNoteReader )
                        MIDIParseNode.trackList.append( newNoteReader.midiTrack )
                    print("Track %s found at byte %s" %(track, byteLoc))
                else:
                    print("THIS ISNT AN MTRK!")
                byteLoc += size
                MIDIParseNode.MIDIFile.seek(size, 1)
            MIDIParseNode.validFile = True
        return #list of track readers
        
        
    def create(self):
        print("create %s"%self)

        self.newInput("an_StringSocket", "File Path", "filePath")
        self.newInput("an_IntegerSocket", "Start Time", "startTime")# in milis
        self.newInput("an_IntegerSocket", "End Time", "endTime")# in milis
        
        self.newOutput("an_MIDITrackListSocket", "Track List", "trackList")
########################################################################################
    def execute(self, filePath, startTime, endTime, ):# error if end time before start time #start is inclusive, end is not
        #print("start execute")                             
        if not filePath == MIDIParseNode.oldPath:                                                 ###CHECK INCLUSIVE EXCLUSIVE LOGIC!
            #print("about to set up!") 
            try:
                self.newFileSetup(filePath)
            except:
                MIDIParseNode.validFile = False
            MIDIParseNode.oldPath = filePath
        read = True
        
        if MIDIParseNode.validFile:
            if startTime == MIDIParseNode.oldStart and endTime == MIDIParseNode.oldEnd:
                return MIDIParseNode.trackList             #The note selection has not changed, use the previous lists. 
                
            if startTime < MIDIParseNode.oldStart:
                for track in MIDIParseNode.trackList:
                    track.clear()#clear lists and search from beginning of the track
                for track in MIDIParseNode.trackReaderList:
                    track.clearBookmark()
                #print("start time was moved back")
            else:
                if endTime < MIDIParseNode.oldEnd and endTime >= MIDIParseNode.oldStart: # second condition not really necessary. for now..
                    for t in MIDIParseNode.trackList: #start at end of lists and remove all times too large
                        t.trimBig(endTime)
                    for track in MIDIParseNode.trackReaderList:
                        track.clearBookmark()
                    read = False
                        #print("read set to false")
                
            #if endTime < #if end time is over file limit
            readerLocMili = startTime
            
            if MIDIParseNode.format == 1 and read :  #will only read format 1 midi files
                tempoList, pulseList, timeList = MIDIParseNode.dataTrack.getTempoSections(startTime, endTime)
                for i in range( 0, len( tempoList ) ):
                    for track in MIDIParseNode.trackReaderList:
                        track.readNotes(pulseList[i], pulseList[i+1], tempoList[i], timeList[i])#(self, startPulse, endPulse, tempo, startTime)
            for track in MIDIParseNode.trackList:
                track.trimSmall(startTime)#clearFinishedNotes()
            MIDIParseNode.oldStart = startTime
            MIDIParseNode.oldEnd = endTime
        
        
        return MIDIParseNode.trackList
        
        
        
        
#################################     TRACK READER CLASSs     ########################################


class trackReader(object):# make vars for absolute time in mili
    def __init__(self, f, start, size, ppqn, Dtime):
        self.file = f#file to read from
        self.trackStart = start #measured in absolute bytes, points to after header
        self.trackSize = size    #measured in bytes
        self.ppqn = ppqn
        self.Dtime = Dtime
        self.tempo = 500000#microseconds per beat (120bpm) as a default
        self.bookmarkPulse, self.bookmarkByte = VLQUnpack32(self.file)
        self.midiTrack = MIDITrack()
        
        self.__choice_table = \
        {
            b'\x80'[0]  : self.noteOff,#note off
            b'\x90'[0]  : self.noteOn,#note on
            b'\xA0'[0]  : self.polyphonicAftertouch,#Polyphonic aftertouch
            b'\xB0'[0]  : self.controlModeChange,#Control mode change (MIDI controlls)
            b'\xC0'[0]  : self.programChange,#Program change
            b'\xD0'[0]  : self.channelAftertouch,#Channel aftertouch
            b'\xE0'[0]  : self.pitchWheelRange,#Pitch wheel range
            b'\xF0'[0]  : self.metaMessage,#System Exclusive
            ###########
            b'\xFF\x00' : self.sequenceNumber,
            b'\xFF\x01' : self.text,
            b'\xFF\x02' : self.copyrightNotice,
            b'\xFF\x03' : self.trackName,
            b'\xFF\x04' : self.instrumentName,
            b'\xFF\x05' : self.lyrics,
            b'\xFF\x06' : self.marker,
            b'\xFF\x07' : self.cuePoint,
            b'\xFF\x20' : self.channelPrefix,
            b'\xFF\x2F' : self.endOfTrack,
            b'\xFF\x51' : self.setTempo,
            b'\xFF\x54' : self.SMPTEoffset,
            b'\xFF\x58' : self.timeSignature,
            b'\xFF\x59' : self.keySignature,
            b'\xFF\x7F' : self.sequencerSpecific
            
        }

    def readMessage(self, f, skip): #returns: bytes Read, callback message, callback data
        msg = f.read(1)
        #print("Message %s at byte %s"%(msg, self.bookmarkByte))
        self.bookmarkByte += 1
        #print("returning the message data")
        return self.__choice_table[msg[0] & 240](f, msg[0], skip, (msg[0] & 15))
        
        
    def noteOff(self, f, com, skip, channel):
        self.file.seek(2,1)
        self.bookmarkByte += 2
    def noteOn(self, f, com, skip, channel):
        self.file.seek(2,1)
        self.bookmarkByte += 2
    def polyphonicAftertouch(self, f, com, skip, channel):
        self.file.seek(2,1)
        self.bookmarkByte += 2
    def controlModeChange(self, f, com, skip, channel):
        self.file.seek(2,1)
        self.bookmarkByte += 2
    def programChange(self, f, com, skip, channel):
        self.file.seek(1,1)
        self.bookmarkByte += 1
    def channelAftertouch(self, f, com, skip, channel):
        self.file.seek(1,1)
        self.bookmarkByte += 1
    def pitchWheelRange(self, f, com, skip, channel):
        self.file.seek(2,1)
        self.bookmarkByte += 2
    def metaMessage(self, f, com, skip, channel):
        msg = self.file.read(1)
        com = b'\xFF' + msg
        self.bookmarkByte += 2 #type and time bytes
        self.__choice_table[com]( f, com, skip, channel )
    ####### META MESSAGE METHODS ######
    def sequenceNumber(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def text(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def copyrightNotice(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def trackName(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def instrumentName(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def lyrics(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def marker(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def cuePoint(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def channelPrefix(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def endOfTrack(self, f, com, skip, channel):#############################   END OF TRCK LOGIC FOR NOTE TRACKS
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def setTempo(self, f, com, skip, channel):
        print("null tempo function executed")
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def SMPTEoffset(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def timeSignature(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def keySignature(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    def sequencerSpecific(self, f, com, skip, channel):
        len = self.file.read(1)
        self.file.seek(len[0],1)
        self.bookmarkByte += len[0]
    
    
    
class NoteReader(trackReader):
    def __init__(self, f, start, size, ppqn, Dtime):
        trackReader.__init__(self, f, start, size, ppqn, Dtime)
        self.startTime = None
        self.startPulse = None
        self.file.seek(self.trackStart)
        self.lastPulse = -1
        
    def clearBookmark(self):
        #if startPulse < self.lastPulse:#back up
            #print(startTime)
            #print("start %s     bookmark %s"%(startPulse, self.bookmarkPulse))
        print("Oh shit, I had to backup :(")
        self.file.seek(self.trackStart)
        self.bookmarkPulse, self.bookmarkByte = VLQUnpack32(self.file)    
    
    def readNotes(self, startPulse, endPulse, tempo, startTime):
        #print("I should stop reading at pulse %s"%endPulse)
        self.tempo = tempo
        self.startTime = startTime
        self.startPulse = startPulse
        self.file.seek(self.trackStart + self.bookmarkByte)#skip to last location
        
        
        self.lastPulse = self.bookmarkPulse
        #lastByte = self.bookmarkByte
        while startPulse > self.bookmarkPulse and self.bookmarkByte < self.trackSize:#catch up
            self.lastPulse = self.bookmarkPulse
            #lastByte = self.bookmarkByte
            self.readMessage(self.file, True)
            pulse, byte = VLQUnpack32(self.file)
            self.bookmarkPulse += pulse
            self.bookmarkByte += byte
        
        print("bookmark is %s track size is %s"%(self.bookmarkByte, self.trackSize))
        while self.bookmarkPulse < endPulse and self.bookmarkByte < self.trackSize:#Read data
            self.lastPulse = self.bookmarkPulse
            #lastByte = self.bookmarkByte
            self.readMessage(self.file, False)
            pulse, byte = VLQUnpack32(self.file)
            self.bookmarkPulse += pulse
            self.bookmarkByte += byte
            
        #self.bookmarkPulse = lastPulse
        #self.bookmarkByte = lastByte
            
        #print("I left my bookmark on byte %s"% self.bookmarkByte)
            
    def noteOff(self, f, com, skip, channel):
        data = self.file.read(2)
        pulse = self.bookmarkPulse - self.startPulse
        time = self.startTime + pulseToMili(self.ppqn, self.tempo, self.Dtime, pulse)#(ppqn, tempo, Dtime, pulses):
        self.midiTrack.noteOff(data[0], data[1], time, channel)
        if skip and len( self.midiTrack.noteData[data[0]] ) > 0:
            #print("skip pop!")
            self.midiTrack.noteData[data[0]].pop()
        self.bookmarkByte += 2
        
    def noteOn(self, f, com, skip, channel):
        #if skip:
        #    self.file.seek(2,1)
        #else:
        data = self.file.read(2)
        pulse = self.bookmarkPulse - self.startPulse
        time = self.startTime + pulseToMili(self.ppqn, self.tempo, self.Dtime, pulse)#(ppqn, tempo, Dtime, pulses):
        #print("startTime %s    time %s    pulse %s    tempo %s"% (self.startTime, time, pulse, self.tempo))
        self.midiTrack.noteOn(data[0], data[1], time, channel)
        self.bookmarkByte += 2

    #def endOfTrack(self, f, com, skip, channel):
        #this is the end
            
            
            
class TempoMapReader(trackReader):# convert time to pulses for the trakcs
    
    def __init__(self, f, start, size, ppqn, Dtime):# maybe add song length var
        trackReader.__init__(self, f, start, size, ppqn, Dtime)
        self.tempos = [500000,]
        self.pulseLoc = [0,]
        self.timeLoc = [0,]
        self.bookmarkTime = pulseToMili(self.ppqn, self.tempo, self.Dtime, self.bookmarkPulse)
        self.getTempoMap()
    
    def getTempoSections(self, startTime, endTime):
        tempoList = []
        pulseList = []
        timeList = []
        indexMod = 1
        index = None
        endIndex = None
        
        for timeInd in range(0, len( self.timeLoc ) ):
            if self.timeLoc[ timeInd ] >= startTime or timeInd == len(self.timeLoc) - 1:# or condition is if its the last tempo of the song.
                if self.timeLoc[ timeInd ] == startTime:#new tempo at start if time location == startTime
                    indexMod = 0
                index = timeInd - indexMod
                endIndex = timeInd - indexMod#this line serves no purpose??
                #print("timeIND %s,    indexMod %s"%(timeInd, indexMod))
                startTempo = self.tempos[ timeInd - indexMod ]
                tempoList.append( startTempo )
                timeList.append(startTime)
                timeFrom = startTime - self.timeLoc[ timeInd - indexMod ]#time from last tempo to start time
               # print("ppqn %s,   tempo %s,  Dtime %s,   timeFrom %s"%(self.ppqn, startTempo, self.Dtime, timeFrom))
                startPulse = self.pulseLoc[ timeInd - indexMod ] + miliToPulse(self.ppqn, startTempo, self.Dtime, timeFrom)
                pulseList.append( startPulse )
                break
        #if index == None:
        #    return None;
        index += 1
        for timeInd in range(index, len( self.timeLoc )):
            if self.timeLoc[ timeInd ] >= endTime:
                endIndex = timeInd - 1
                break
            tempoList.append( self.tempos[ timeInd ] )
            pulseList.append( self.pulseLoc[ timeInd ] )
            timeList.append( self.timeLoc[ timeInd ] )
        timeFrom = endTime - self.timeLoc[ endIndex ] 
        pulseList.append( self.pulseLoc[ endIndex ] + miliToPulse(self.ppqn, self.tempos[ endIndex ], self.Dtime, timeFrom) ) 
        return tempoList, pulseList, timeList
                
                
                
    
    def getTempoMap(self):
        print("Start of get tempo map")
        end = self.trackSize - 1 
        print("a")
        while self.bookmarkByte < end:
            print("b")
            self.readMessage(self.file, False)
            print("c")
            pulse, byte = VLQUnpack32(self.file)
            print("d")
            self.bookmarkPulse += pulse
            print("e")
            self.bookmarkByte += byte
        #print(self.pulseLoc)
        #print(self.tempos)
        #print(self.timeLoc)
            
    def setTempo(self, f, com, skip, channel):
        print("set tempo called")
        length = self.file.read(1)
        tempo = self.file.read(3)
        self.tempo = int.from_bytes(tempo, byteorder='big')
        lastPulse = self.pulseLoc[ len(self.pulseLoc) - 1 ]
        if self.bookmarkPulse == lastPulse:
            self.tempos.pop()
        else:
            lastTempo = self.tempos[ len(self.tempos) - 1 ]
            lastTime = self.timeLoc[ len(self.timeLoc) - 1 ]
            Dpulse = self.bookmarkPulse - lastPulse
            self.timeLoc.append( lastTime + pulseToMili(self.ppqn, lastTempo, self.Dtime, Dpulse) )
            self.pulseLoc.append(self.bookmarkPulse)
        self.tempos.append(self.tempo)
        self.bookmarkByte += length[0]

        
        
        
        
        
   