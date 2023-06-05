section .text
    global _main

_main:
    mov eax, esp
    push DWORD [anonymous.1]
    push DWORD [anonymous.1+4]
    call [eax]
    _break.1:
    ret

anonymous.1:
    mov eax, 4
    ret