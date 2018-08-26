import bpy
from bpy.props import *
from .. data_structures.MIDITrack import MIDITrack
from .. base_types.socket import AnimationNodeSocket
from .. events import propertyChanged

class MIDITrackSocket(bpy.types.NodeSocket, AnimationNodeSocket):
    bl_idname = "an_MIDITrackSocket"
    bl_label = "MIDI Track Socket"
    dataType = "MIDITrack"
    allowedInputTypes = ["MIDITrack"]
    drawColor = (1.0, 0.5, 0.5, 1)
    storable = True
    comparable = False
    
    @classmethod
    def getDefaultValue( cls ):
        return MIDITrack()
        
    @classmethod
    def correctValue(cls, value):
        if isinstance(value, MIDITrack):
            return value, 0
        else:
            #try: return Matrix(value), 1
            #except: 
            return cls.getDefaultValue(), 2
            
            
class MIDITrackListSocket(bpy.types.NodeSocket, AnimationNodeSocket):
    bl_idname = "an_MIDITrackListSocket"
    bl_label = "MIDI Track List Socket"
    dataType = "MIDITrack List"
    baseDataType = "MIDITrack"
    allowedInputTypes = ["MIDITrack List"]
    drawColor = (1, 0.5, 0.5, 0.5)
    storable = True
    comparable = False

    @classmethod
    def getDefaultValue(cls):
        return []

    @classmethod
    def getDefaultValueCode(cls):
        return "[]"

    @classmethod
    def getCopyExpression(cls):
        return "[element.copy() for element in value]"

    @classmethod
    def correctValue(cls, value):
        if isinstance(value, list):
            if all(isinstance(element, MIDITrack) for element in value):
                return value, 0
        #try: return [Matrix(element) for element in value], 1
        #except: 
        return cls.getDefaultValue(), 2
