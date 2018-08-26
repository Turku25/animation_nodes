import bpy
from bpy.props import *
from .. data_structures.MIDINote import MIDINote
from .. base_types.socket import AnimationNodeSocket
from .. events import propertyChanged

class MIDINoteSocket(bpy.types.NodeSocket, AnimationNodeSocket):
    bl_idname = "an_MIDINoteSocket"
    bl_label = "MIDI Note Socket"
    dataType = "MIDINote"
    allowedInputTypes = ["MIDINote"]
    drawColor = (0.75, 1.0, 0.5, 1)
    storable = True
    comparable = False
    
    @classmethod
    def getDefaultValue( cls ):
        return MIDINote(0, 0, 0)
        
    @classmethod
    def correctValue(cls, value):
        if isinstance(value, MIDINote):
            return value, 0
        else:
            #try: return Matrix(value), 1
            #except: 
            return cls.getDefaultValue(), 2
            
            
class MIDINoteListSocket(bpy.types.NodeSocket, AnimationNodeSocket):
    bl_idname = "an_MIDINoteListSocket"
    bl_label = "MIDI Note List Socket"
    dataType = "MIDINote List"
    baseDataType = "MIDINote"
    allowedInputTypes = ["MIDINote List"]
    drawColor = (0.75, 1.0, 0.5, 0.5)
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
            if all(isinstance(element, MIDINote) for element in value):
                return value, 0
        #try: return [Matrix(element) for element in value], 1
        #except: 
        return cls.getDefaultValue(), 2
