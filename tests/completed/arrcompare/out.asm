
global _main

section .bss

section .text
_write:
push ebp
mov ebp, esp
sub esp, 0

xor eax, eax
pop ebp
ret
pop ebp
ret
_main:
push ebp
mov ebp, esp
sub esp, 16

mov DWORD [ebp-12], 10
xor eax, eax
mov [ebp-8], eax
lea eax, [ebp-12]
mov [ebp-4], eax
push DWORD [ebp-4]
lea eax, [_write]
call eax
add esp, 4
xor eax, eax
mov esp, ebp
pop ebp
ret
mov esp, ebp
pop ebp
ret

section .data
