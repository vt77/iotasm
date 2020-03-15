"""
Wirebus virtual machine bytecode compiler

This project is a part of wirebus computing system.
For more info refer to https://github.com/vt77/wirebus 

Author: Daniel Marchasin 
License: MIT

"""

import logging
logger = logging.getLogger(__name__)

import math

from .stackmachine import commands


class CompileException(Exception):
    def __init__(self,line,message):
        logger.error("Compiler error in line %s : %s",line,message)
        super().__init__(message)
        self.line = line
        self.error = message

class LinkException(Exception):
    pass

def compile(script_filename,registersize=8):
    """ Compile to bytecode. Input : filename (iot.src) Retruns bytes() """
    with open(script_filename,"rt") as f:
        lines_count = 0
        code_segment = []
        code_segment_ptr = 0
        labels = {}
        vars = []
        vars_init = {}
        constants = {}

        if registersize not in [8,16,32,64]:
            raise CompileException(("Wrong register size %d. Should be one of [8,16,32,64]" % registersize))

        MAX_NUMBER = int(math.pow(2,registersize))

        logger.info("Compile script %s for arch %s bits MAX_NUMBER(%s)",script_filename,registersize*8,MAX_NUMBER)

        for line in f.read().splitlines():
            lines_count += 1
            if line.startswith(';') or len(line)==0:
                continue
            logger.debug("Process line : %s",line )

            if line.startswith(':'):
                label_name = line.rstrip()[1:]
                logger.debug("Found label : %s Line %s", label_name, 1)
                labels[label_name] = code_segment_ptr
                continue

            if line.startswith('LET'):
                ''' Preprocessor for vars_init'''
                (_,var_name,value) = line.split()
                logger.debug("Found variable %s" , var_name )
                value = int(value)
                if value > MAX_NUMBER:
                    raise LinkException("Number %s to big for architecture %s bit" % (value,registersize*8))
                vars_init[var_name]=value
                vars.append(str(var_name))
                continue

            if line.startswith('CONST'):
                ''' Preprocessor for constants '''
                (_,const_name,value) = line.split()
                logger.debug("Found constant %s" , const_name )
                constants[const_name] = value
                continue

            if line.startswith(tuple(commands.keys())):
                command = line.split();
                logger.debug("Process script command %s" , command[0] )
                cmd_data = commands[command[0]]
                if cmd_data[1] > 0 and len(command) == 1:
                    raise CompileException(lines_count,"Command %s has %s parameter(s) but none present" % command[0], cmd_data[1])
                     
                code_segment.append(str(cmd_data[0]))

                if cmd_data[1] > 0:
                    param = None
                    if cmd_data[2] == 'C':   #Constant
                         if command[1] in constants:
                            param = str(constants[command[1]])
                         elif command[1].isnumeric():
                            param = str(command[1])
                         else:
                            CompileException(lines_count,"Wrong constant value : %s" % (command[1]))

                         if int(param) > MAX_NUMBER:
                            raise LinkException("Number %s to big for architecture %s bit" % (param,registersize*8))

                    elif cmd_data[2] == 'A': #variable (address in dataspace)
                        param = 'var:%s' % command[1]
                    elif cmd_data[2] == 'L': #Label
                        param = "label:%s" % (command[1])
                    else:
                        raise CompileException(lines_count,"Unknown variable type %s" % cmd_data[2])

                    if param is None:
                        raise CompileException(lines_count,"Parameter manditory but not present %s" % line)

                    code_segment.append(param)
                
                code_segment_ptr =  len(code_segment)
                continue

            raise CompileException(lines_count,"Line %s - unknown command" % (line) )


        ''' Link the code ''' 
        compiled_data = []
        data_segment_start = len(code_segment)
        for bytecode in code_segment:
            if bytecode.startswith('label:'):
                (_,label) = bytecode.split(':')
                logger.debug("Link Label : %s" ,label )
                bytecode = labels.get(label)
                if bytecode is None:
                    LinkException("Label not found %s" % label) 
            elif bytecode.startswith('var:'):
                (_,var) = bytecode.split(':')
                if var not in vars:
                    vars.append(var)
                bytecode = data_segment_start + vars.index(var)
            compiled_data.append(int(bytecode))

        for var_name in vars:
             compiled_data.append(vars_init.get(var_name,0))
       
        logger.info("Compile script done: Code %d byte(s). Data %d byte(s)",data_segment_start,len(vars))
        return compiled_data

    return None
