import bpy
#from ... data_structures.MIDITrack import MIDITrack
from ... data_structures.MIDINote import MIDINote
from ... base_types.node import AnimationNode

class MIDIDecomposeNote(bpy.types.Node, AnimationNode):
    bl_idname = "MIDIDecomposeNote"
    bl_label = "Decompose MIDI Note"
    
        
    def create(self):
        self.newInput("an_MIDINoteSocket", "Note", "Note")
        
        self.newOutput("an_IntegerSocket", "Note Value", "value")
        self.newOutput("an_IntegerSocket", "Start Time", "startTime")
        self.newOutput("an_IntegerSocket", "Duration", "duration")
        self.newOutput("an_IntegerSocket", "Velocity", "velocity")

        
        
        #self.note = noteValue
        #self.startTime = start
        #self.duration = -1
        #self.vel = velocity
        
    def execute(self, Note ):
        
        return Note.note, Note.startTime, Note.duration, Note.vel
 