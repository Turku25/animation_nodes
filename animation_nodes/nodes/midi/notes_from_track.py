import bpy
from ... data_structures.MIDITrack import MIDITrack
from ... data_structures.MIDINote import MIDINote
from ... base_types.node import AnimationNode

class MIDINotesFromTrack(bpy.types.Node, AnimationNode):
    bl_idname = "MIDINotesFromTrack"
    bl_label = "MIDI Notes From Track"
    
        
    def create(self):
        self.newInput("an_MIDITrackSocket", "Track", "track")
        
        self.newOutput("an_MIDINoteListSocket", "Note List", "noteList")

    def execute(self, track ):
        notes = []
        for noteRow in track.noteData:
            for note in noteRow:
                notes.append(note)
        return notes
 