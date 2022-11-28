
extern _STRING_CONSTANT
extern _puts
global _main

section .bss

section .text
_main:
	push ebx
	push esi
	sub esp, 8
	
	mov eax, _STRING_CONSTANT ; had to manually remove the deference from this because the language currently has no mechanism for ref or deref
	push eax
	call _puts
	add esp, 4
	xor eax, eax
	add esp, 8
	pop esi
	pop ebx
	ret
	add esp, 8
	pop esi
	pop ebx
	ret

section .data