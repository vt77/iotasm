
import os
import logging
logger = logging.getLogger(__name__)


import struct

class sfmt():
    def __init__(self,format,size,endian='<'):
        self.f = (endian,format,size)
    def get_byte_size(self):
        return self.f[2]
    def get_format(self):
        return self.f[1]
    def get_format_string(self,L):
        return self.f[0]+self.f[1]*L

class scriptformat:
    b8=sfmt('B',1)
    b16=sfmt('H',2)
    b32=sfmt('I',4)

def load_script_file(script_filename,format=None):
    logger.info("[LOADER]Loading script %s",script_filename)
    statinfo = os.stat(script_filename)
    script_size = statinfo.st_size 
    with open(script_filename,"rb") as f: 
        commands_count = int(f.read(1)[0])
        _data = f.read()

    if format is None:
        registersize = (script_size-1) // commands_count
        format = getattr(scriptformat,"b"+str(registersize*8))  
    return(struct.unpack(format.get_format_string(commands_count),_data))

def save_script_file(script_filename,bytecode,format=scriptformat.b8):
    logger.info("[LOADER]Save %s",script_filename)
    with open(script_filename,"wb") as f:
        script_len = len(bytecode)
        f.write(bytes([script_len]))
        f.write(struct.pack(format.get_format_string(script_len),*bytecode))
