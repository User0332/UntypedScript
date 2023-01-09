
extern _printf
extern _NORMAL_ARRAY_BYTE_OFFSET
extern _value_at
global _main

section .bss

section .text
_main:
	push ebp
	mov ebp, esp
	sub esp, 16
	mov eax, [esp+24]
	mov [ebp-4], eax
	mov eax, [esp+28]
	mov [ebp-0], eax
	
	xor eax, eax
	mov [ebp-8], eax
	mov eax, [ebp-4]
	push eax
	mov eax, string.0
	push eax
	call _printf
	add esp, 8
	.while.1:
	mov eax, [ebp-8]
	push eax
	mov eax, [ebp-4]
	pop ebx
	cmp ebx, eax
	setl al
	movzx eax, al
	cmp eax, 0
	je .cont.1
	mov eax, [ebp-8]
	push eax
	mov eax, [ebp-0]
	push eax
	call _value_at
	add esp, 8
	mov [ebp-12], eax
	mov eax, [ebp-12]
	push eax
	mov eax, [ebp-8]
	push eax
	mov eax, string.2
	push eax
	call _printf
	add esp, 12
	mov eax, [ebp-8]
	push eax
	mov eax, 1
	pop ebx
	add ebx, eax
	mov eax, ebx
	mov [ebp-8], eax
	jmp .while.1
	.cont.1:
	xor eax, eax
	add esp, 16
	pop ebp
	ret
	add esp, 16
	pop ebp
	ret

section .data
	string.0 db 97, 114, 103, 99, 32, 61, 32, 37, 105, 10, 0
	string.2 db 97, 114, 103, 118, 91, 37, 105, 93, 32, 61, 32, 37, 115, 10, 0