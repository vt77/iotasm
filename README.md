IoT-PLC assembler
 ---
 
 ## Overview
 This project is a very-very simple assembler-like scripting language (that's you see in Instruction List of real PLC), compiler and virtual machine to debug compiled scripts.   It's purpose  to bring ladder logic to small microcontrollers like ESP, ATMega, PIC16 and same.  
 
 
 ## Disclaimer
 This project is a part of our multi-functional  *IoT contorller*. That's the reason why so many "IoT" in here. There is no microcontroller's code included. Only basic scripting concept, compiler and test environment.  It may work partially or may not work at all for you, fit your requirments or not. There is no support for this code.  
After all if you find this code useful no matter what, you can use it free of charge, conditions, restrictions or any other obstacles. No strings  
And, yes... I really like assembler
 
 ## Arcitecture and Limitations 
 
 The scripts runs on 8-bit virtual *stack machine*. It means variables limited to 8bit integer(signed). There is no MUL and DIV commands. Command may have *maximum* 1 parameter. 
 
 Virtual machine has two memory segments for code and variables. Variables preserved between script sessions. Default value for the variable may be set in compile-time.  
 
Stack size  unlimited in debugger environment . In microcontroller 8-16 bytes stack size should be good for most tasks. 
 
There is two abstract commands IN and OUT  to work with external "ports". Port is a virtual *endpoint* in host device. It may send or receive data into script, usually from peripheral. Command parameter unsigned 8 bit integer, it means you may have up to 256 IO "ports".  
 
 
 
 ## Commands and types
 
  
 
 ### Types

Type  | Description | Type
------------- | -------------|-----------
C  | Constant   | Numeric 8 bit
A  | Variable (address)  |  alphanumeric 
L  |Label  | :alphanumeric



 ### Precompiler derectives
 
 Precompiler derectives should be defined in beginig of script.  
 
 Derective  |  Description | Example 
------------- | -------------|-----------
CONST  |  Defines constant |  CONST  HYSTERESIS   5
LET  |  Defines variable. * |  LET timer_value 0

*The value of variable will be saved in script's data section

 
 ### Iot Assembler
 
  Command   |  ParamType |Description |  Stack Change 
------------- |:------:|-------------|----------- 
 **NOP** |  - |No Operation |  Unchanged
**PUSHI**  |  C | Push constant to stack |  stack.push(c)
**LOAD**  |  A | Load value from address A |  stack.push(vars[a])
**STOR**  |  A | Stores top of stack in address A |  vars[a] = stack.pop()
**DUP**  |  - |  Duplicates top stack element |  stack.push(stack[0])
**SWAP**  |  - |  Swap top two elements of stack |  stack[0] <=> stack[1]
**ADD**  |  - |  Add the top two elements on the stack |  stack.push(stack.pop()+stack.pop())
**ADDI**  | C |  Add indirect, top element plus constant |  stack.push(stack.pop()+C)
**SUB**  |  - |  Add the top two elements on the stack |  stack.push(stack.pop(1)-stack.pop(0))
**SUBI**  | C |  Add indirect, top element plus constant |  stack.push(stack.pop()-C)
**CMP**  |  - |  Compare. Alias for SUB |  -
**CMPI**  | C |  Compare indirect. Alias for SUBI |  -
**JMP**  | L |  Unconditional jump |  Unchanged
**JMPEQ**  | L |  Jump if top element is 0 |  stack.pop()
**JMPLT**  | L |  Jump if top element  < 0 |  stack.pop()
**JMPGE**  | L |  Jump if top element  > 0 |  stack.pop()
**RETURN**  | - |  See *Return from script* |  stack.pop()
**IN**  | C |  See: *Host device exchange* |  stack.push(value_from_device)
**OUT**  | C |  See: *Host device exchange* |  stack.pop()


 ### Host device exchange
 Sometime script should interact with host device to get/send data to it. Thats the virtual "ports" used for. The port is just virtual address sent to device with IN/OUT command. One unsigned 8 bit custom parameter may be sent. 
 
For example:  Let's say we want to control on/off realy. We define virtual "port" 10  on host microcontroller responsible to control relay pin. So in script you can execute following commands to send "1" to "port" 

```
PUSHI 1
OUT 10
```
 
 Another example. Let's imagine port 12 is a temperature sensor.  So you can simple write:
 
 ```
 
IN 12  ;Read temperature
;Now temperature on top of stack
CMPI  TEMPERATURE_LIMIT
JMPLT switch_device_on
JMP out

:switch_device_on
PUSHI 1
OUT 10

:out
;Get relay status and return
IN 10
RETURN

```
 

 
 
 ### Return from script
 Script runs till command RETURN reached. Command pops element from stack and returns this value to the host controller
 
 
 ## Examples
 See *examples* directory 
 
 

## License
MIT License. See License.txt for more info


