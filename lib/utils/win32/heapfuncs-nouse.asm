
extern _printf
extern _abort
extern _VirtualAlloc@16
extern _VirtualProtect@16
extern _VirtualFree@12
global _HeapFuncAlloc
global _HeapFuncProtect
global _HeapFuncFree

section .bss
dumpvar.0 resd 1

section .text
_HeapFuncAlloc:
push ebp
mov ebp, esp
sub esp, 4
push DWORD [_WINDOWS_H_PAGE_READWRITE]
push DWORD [_WINDOWS_H_MEM_COMMIT_RESERVE]
push DWORD [ebp+8]
xor eax, eax
push eax
lea eax, [_VirtualAlloc@16]
call eax
mov [ebp-4], eax
push DWORD [ebp-4]
xor eax, eax
pop ebx
cmp ebx, eax
sete al
movzx eax, al
cmp eax, 0
jne .if.1
jmp .else.1
.if.1:
push DWORD [ebp+8]
push DWORD string.2 ; string 'UntypedScript fatal -> failed to allocate memory for heapfunction using VirtualAlloc (returned NULL)\n\tcalled VirtualAlloc(0, %d, 12288, 4)\n'
lea eax, [_printf]
call eax
add esp, 8
lea eax, [_abort]
call eax
add esp, 0
jmp .cont.1
.else.1:
.cont.1:
mov eax, [ebp-4]
mov esp, ebp
pop ebp
ret
_HeapFuncProtect:
push ebp
mov ebp, esp
sub esp, 4
xor eax, eax
mov [ebp-4], eax
lea eax, [ebp-4]
push eax
push DWORD [_WINDOWS_H_PAGE_EXECUTE_READ]
push DWORD [ebp+12]
push DWORD [ebp+8]
lea eax, [_VirtualProtect@16]
call eax
push eax
xor eax, eax
pop ebx
cmp ebx, eax
sete al
movzx eax, al
cmp eax, 0
jne .if.4
jmp .else.4
.if.4:
lea eax, [ebp-4]
push eax
push DWORD [ebp+12]
push DWORD [ebp+8]
push DWORD string.5 ; string 'UntypedScript fatal -> failed to protect memory for heapfunction using VirtualProtect (returned 0)\n\tcalled VirtualProtect(0x%p, %d, 32, 0x%p)\n'
lea eax, [_printf]
call eax
add esp, 16
push DWORD [ebp-4]
push DWORD string.6 ; string 'Old protection value=%d'
lea eax, [_printf]
call eax
add esp, 8
lea eax, [_abort]
call eax
add esp, 0
jmp .cont.4
.else.4:
.cont.4:
mov eax, [ebp+8]
mov esp, ebp
pop ebp
ret
_HeapFuncFree:
push ebp
mov ebp, esp
sub esp, 0
push DWORD [_WINDOWS_H_MEM_RELEASE]
xor eax, eax
push eax
push DWORD [ebp+8]
lea eax, [_VirtualFree@12]
call eax
push eax
xor eax, eax
pop ebx
cmp ebx, eax
sete al
movzx eax, al
cmp eax, 0
jne .if.8
jmp .else.8
.if.8:
push DWORD [ebp+8]
push DWORD string.9 ; string 'UntypedScript fatal -> failed to release memory for heapfunction using VirtualFree (returned 0)\n\tcalled VirtualFree(0x%p, 0, 32768)\n'
lea eax, [_printf]
call eax
add esp, 8
lea eax, [_abort]
call eax
add esp, 0
jmp .cont.8
.else.8:
.cont.8:
xor eax, eax
pop ebp
ret

section .data
_WINDOWS_H_MEM_COMMIT_RESERVE dd 12288
_WINDOWS_H_PAGE_EXECUTE_READ dd 32
_WINDOWS_H_PAGE_READWRITE dd 4
_WINDOWS_H_MEM_RELEASE dd 32768
string.2 db 85, 110, 116, 121, 112, 101, 100, 83, 99, 114, 105, 112, 116, 32, 102, 97, 116, 97, 108, 32, 45, 62, 32, 102, 97, 105, 108, 101, 100, 32, 116, 111, 32, 97, 108, 108, 111, 99, 97, 116, 101, 32, 109, 101, 109, 111, 114, 121, 32, 102, 111, 114, 32, 104, 101, 97, 112, 102, 117, 110, 99, 116, 105, 111, 110, 32, 117, 115, 105, 110, 103, 32, 86, 105, 114, 116, 117, 97, 108, 65, 108, 108, 111, 99, 32, 40, 114, 101, 116, 117, 114, 110, 101, 100, 32, 78, 85, 76, 76, 41, 10, 9, 99, 97, 108, 108, 101, 100, 32, 86, 105, 114, 116, 117, 97, 108, 65, 108, 108, 111, 99, 40, 48, 44, 32, 37, 100, 44, 32, 49, 50, 50, 56, 56, 44, 32, 52, 41, 10, 0 ; string 'UntypedScript fatal -> failed to allocate memory for heapfunction using VirtualAlloc (returned NULL)\n\tcalled VirtualAlloc(0, %d, 12288, 4)\n'
function.0.ALLOCATED_BYTES equ 4
string.5 db 85, 110, 116, 121, 112, 101, 100, 83, 99, 114, 105, 112, 116, 32, 102, 97, 116, 97, 108, 32, 45, 62, 32, 102, 97, 105, 108, 101, 100, 32, 116, 111, 32, 112, 114, 111, 116, 101, 99, 116, 32, 109, 101, 109, 111, 114, 121, 32, 102, 111, 114, 32, 104, 101, 97, 112, 102, 117, 110, 99, 116, 105, 111, 110, 32, 117, 115, 105, 110, 103, 32, 86, 105, 114, 116, 117, 97, 108, 80, 114, 111, 116, 101, 99, 116, 32, 40, 114, 101, 116, 117, 114, 110, 101, 100, 32, 48, 41, 10, 9, 99, 97, 108, 108, 101, 100, 32, 86, 105, 114, 116, 117, 97, 108, 80, 114, 111, 116, 101, 99, 116, 40, 48, 120, 37, 112, 44, 32, 37, 100, 44, 32, 51, 50, 44, 32, 48, 120, 37, 112, 41, 10, 0 ; string 'UntypedScript fatal -> failed to protect memory for heapfunction using VirtualProtect (returned 0)\n\tcalled VirtualProtect(0x%p, %d, 32, 0x%p)\n'
string.6 db 79, 108, 100, 32, 112, 114, 111, 116, 101, 99, 116, 105, 111, 110, 32, 118, 97, 108, 117, 101, 61, 37, 100, 0 ; string 'Old protection value=%d'
function.3.ALLOCATED_BYTES equ 4
string.9 db 85, 110, 116, 121, 112, 101, 100, 83, 99, 114, 105, 112, 116, 32, 102, 97, 116, 97, 108, 32, 45, 62, 32, 102, 97, 105, 108, 101, 100, 32, 116, 111, 32, 114, 101, 108, 101, 97, 115, 101, 32, 109, 101, 109, 111, 114, 121, 32, 102, 111, 114, 32, 104, 101, 97, 112, 102, 117, 110, 99, 116, 105, 111, 110, 32, 117, 115, 105, 110, 103, 32, 86, 105, 114, 116, 117, 97, 108, 70, 114, 101, 101, 32, 40, 114, 101, 116, 117, 114, 110, 101, 100, 32, 48, 41, 10, 9, 99, 97, 108, 108, 101, 100, 32, 86, 105, 114, 116, 117, 97, 108, 70, 114, 101, 101, 40, 48, 120, 37, 112, 44, 32, 48, 44, 32, 51, 50, 55, 54, 56, 41, 10, 0 ; string 'UntypedScript fatal -> failed to release memory for heapfunction using VirtualFree (returned 0)\n\tcalled VirtualFree(0x%p, 0, 32768)\n'
function.7.ALLOCATED_BYTES equ 0
