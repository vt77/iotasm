"""
Virtual machine for wirebus IoT PLC

This project is a part of wirebus computing system.
For more info refer to https://github.com/vt77/wirebus 

Author: Daniel Marchasin 
License: MIT

"""

import logging
from functools import partial

logger = logging.getLogger(__name__)


'''
Simple iot assmbler commands and types 

 C - constant 
 A - address (virtual memory location)
 L - label 

PUSHI C  Push constant to stack
LOAD A  Load from address A and push
STOR A  Store top of stack in address A
DUP     Duplicate top of stack
SWAP    Swap top two elements of stack 
ADD     Add the top two elements on the stack.
ADDI C  Add indirect, top element plus constant
SUB     Subtract top two elements of stack
SUBI C  Substruct constant from top element
CMP     Compare. Alias for SUB
CMPI    Compare indirect. Alias for SUBI
JMP   L Non-conditional jamp
JMPEQ  L  Jump if top element is 0
JMPLE  L Jump if top element < 0
JMPGE  L Jump if top element > 0
RETURN  Returns top of the stack to caller
DEVICE  Device manipulation (for more info see README file)

Commands list:

Each command is a tuple of (opcode,params_count,param_type)
This structure used by compiler to generate bytecode
'''
commands = {
    'NOP':(0,0),
    'PUSHI':(1,1,'C'),
    'LOAD':(2,1,'A'),
    'STOR':(3,1,'A'),
    'DUP':(4,0),
    'SWAP':(5,0),
    'ADD':(6,0),
    'ADDI':(7,1,'C'),
    'SUB':(8,0),
    'SUBI':(9,1,'C'),
    'CMP':(8,0),
    'CMPI':(9,1,'C'),
    'JMP':(10,1,'L'),
    'JMPEQ':(11,1,'L'),
    'JMPLT':(12,1,'L'),
    'JMPGT':(13,1,'L'),
    'RETURN':(14,0),
    'OUT':(15,1,'C'),
    'IN':(16,1,'C')
}


'''
Commands handlers
'''

def op_nop(vm):
    ''' No operation '''
    logger.debug("Process NOP")
    return vm.reg_ip+1

def op_pushi(vm):
    ''' Push constant'''
    val = vm.peek_param(1)
    logger.debug("Process PUSHI %d",val)
    vm.stack_push(val)
    return vm.reg_ip+2

def op_load(vm):
    ''' Load from var'''
    addr = vm.peek_param()
    val  = vm.peek_data(addr)
    logger.debug("Process LOAD %s => %s",addr,val)
    vm.stack_push(val)
    return vm.reg_ip+2

def op_stor(vm):
    ''' Store to var '''
    addr = vm.peek_param()
    val = vm.stack_pop()
    logger.debug("Process STOR %d => %d",val,addr)
    vm.poke_data(addr,val)
    return vm.reg_ip+2

def op_dup(vm):
    ''' Duplicate top stack value '''
    logger.debug("Process DUP")
    val = vm.peek_stack()
    vm.stack_push(val)
    return vm.reg_ip + 1 

def op_swap(vm):
    ''' Swap two topmost stack values '''
    val1 = vm.stack_pop()
    val2 = vm.stack_pop()
    logger.debug("Process SWAP %d <=> %d",val1,val2)
    vm.stack_push(val1)
    vm.stack_push(val2)
    return vm.reg_ip+1

def op_add(vm):
    ''' Add constant stack[0] = stack[1] + stack[0]  '''
    val1 = vm.stack_pop()
    val2 = vm.stack_pop()
    logger.debug("Process ADD %d + %d",val1,val2)
    vm.stack_push(val1+val2)
    return vm.reg_ip+1

def op_addi(vm):
    ''' Add constant  '''
    logger.debug("Process ADDI")
    val1 = vm.peek_param()
    val2 = vm.stack_pop()
    vm.stack_push(val1+val2)
    return vm.reg_ip+2

def op_sub(vm):
    ''' Subtract stack[0] = stack[1] - stack[0]   '''
    val1 = vm.stack_pop()
    val2 = vm.stack_pop()
    logger.debug("Process SUB %d - %d",val2,val1)
    vm.stack_push(val2-val1)
    return vm.reg_ip+1

def op_subi(vm):
    ''' Subtract constant  '''
    logger.debug("Process SUBI")
    vm.stack_push(vm.peek_param())
    return op_sub(vm)+1

''' Unconditional jump '''
def op_jmp(vm):
    ''' Unconditional jump '''
    addr = vm.peek_param() 
    logger.debug("Process JMP %d",addr)
    return addr

''' jump if equals '''
def op_jmpeq(vm):
    ''' jump if equals '''
    param = vm.stack_pop()
    logger.debug("Process JMPEQ %d %s",param,param==0)
    return op_jmp(vm) if param == 0 else vm.reg_ip+2 

''' jump if less '''
def op_jmplt(vm):
    ''' jump if less '''
    param = vm.stack_pop()
    logger.debug("Process JMPLE %d %s",param,param<0)
    return op_jmp(vm) if param < 0 else vm.reg_ip+2

''' jump if greater '''
def op_jmpgt(vm):
    ''' jump if greater '''
    param = vm.stack_pop()
    logger.debug("Process JMPGE %d %s",param,param>0)
    return op_jmp(vm) if param > 0 else vm.reg_ip+2


def call_device(isout,vm):
    ''' Custom function . See docs for more info '''
    from __main__ import device
    port_num =  vm.peek_param()
    if isout:
        device.port_out(port_num,vm.stack_pop())
    else:
        vm.stack_push(device.port_in(port_num))
    return vm.reg_ip+2

''' Commands dispatcher '''
functions = [
        op_nop,         #0
        op_pushi,       #1
        op_load,        #2
        op_stor,        #3
        op_dup,         #4
        op_swap,        #5
        op_add,         #6
        op_addi,        #7
        op_sub,         #8
        op_subi,        #9
        op_jmp,         #10
        op_jmpeq,       #11
        op_jmplt,       #12
        op_jmpgt,       #13
        None,           #14 //Return
        partial(call_device,True),      #15 //Out
        partial(call_device,False)       #16 //In
]


class VirtualCPU:
    ''' Virtual CPU '''
    def __init__(self,script):
        ''' Initilize. Params :  compiled script'''
        self.script = list(script)
        self.reset()

    @property
    def reg_ip(self):
        return self.__instr_ptr

    def step(self):
        ''' Runs one step of program '''
        cmd = self.script[self.__instr_ptr]
        if cmd == 14: #RETURN
            self.done = True
            return self.stack_pop()
        logger.debug("Process ip:%d cmd %s",self.__instr_ptr,functions[self.script[self.__instr_ptr]]) 
        self.__instr_ptr = functions[cmd](self) 
        return None

    def reset(self):
        ''' Resets CPU. Script memory preserved while reset '''
        self.stack = []
        self.done = False
        self.__instr_ptr = 0
    
    def start(self,params=[]):
        ''' Start script. Params - initial stack(script params) '''
        self.stack = params
        
    def stack_pop(self):
        ''' Pop byte from stack '''
        return self.stack.pop(0)

    def stack_push(self,val):
        ''' Push byte to stack '''
        self.stack.insert(0,val)

    ''' NOTE: reverse  name convertion has a secret meaning :). '''
    def peek_param(self,pos=1):
        ''' Peek opcode param from code section '''
        return self.script[self.__instr_ptr+pos]

    def peek_stack(self,pos=0):
        ''' Peek from stack (stack unchanged) '''
        return self.stack[pos]

    def peek_data(self,addr):
        ''' Peeks var from data section '''
        return self.script[addr]
    def poke_data(self,addr,val):
        ''' Pokes var to data section '''
        self.script[addr] = val




def run(script,params=[]):
    ''' Run script on virtual CPU '''
    logger.debug("Start script")

    vm = VirtualCPU(script)
    vm.reset()
    vm.start(params)

    while not vm.done:
      retcode = vm.step()     
      logger.debug("Stack after call %s" % (vm.stack) )
    logger.debug("Script return %s" % (retcode) )
    return retcode
