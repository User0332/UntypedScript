
extern _puts
extern _printf
extern _sleep
global _main

section .bss

section .text
_my_other_func:
	push ebp
	mov ebp, esp
	sub esp, 0
	
	mov eax, 0
	pop ebp
	ret
	pop ebp
	ret
anonymous.2:
	push ebp
	mov ebp, esp
	sub esp, 0
	
	mov eax, string.0
	push eax
	lea eax, [_puts]
	call eax
	add esp, 4
	mov eax, string.1
	pop ebp
	ret
	pop ebp
	ret
_main:
	push ebp
	mov ebp, esp
	sub esp, 8
	
	mov eax, 5
	mov [ebp-4], eax
	mov eax, anonymous.2
	mov [ebp-8], eax
	mov eax, string.3
	push eax
	lea eax, [_puts]
	call eax
	add esp, 4
	mov eax, [ebp-4]
	push eax
	mov eax, string.4
	push eax
	lea eax, [_printf]
	call eax
	add esp, 8
	mov eax, string.5
	push eax
	lea eax, [_puts]
	call eax
	add esp, 4
	mov eax, 1
	push eax
	lea eax, [_sleep]
	call eax
	add esp, 4
	mov eax, string.6
	push eax
	lea eax, [_puts]
	call eax
	add esp, 4
	lea eax, [_my_other_func]
	call eax
	add esp, 0
	push eax
	mov eax, string.7
	push eax
	lea eax, [_printf]
	call eax
	add esp, 8
	lea eax, [ebp-8]
	call eax
	add esp, 0
	push eax
	mov eax, string.8
	push eax
	lea eax, [_printf]
	call eax
	add esp, 8
	mov eax, 0
	mov esp, ebp
	pop ebp
	ret
	mov esp, ebp
	pop ebp
	ret

section .data
	string.0 db 116, 104, 105, 115, 32, 105, 115, 32, 105, 110, 32, 97, 110, 32, 105, 110, 110, 101, 114, 32, 102, 117, 110, 99, 116, 105, 111, 110, 33, 0
	string.1 db 116, 104, 105, 115, 32, 115, 116, 114, 105, 110, 103, 33, 0
	string.3 db 72, 101, 108, 108, 111, 44, 32, 87, 111, 114, 108, 100, 33, 0
	string.4 db 120, 32, 105, 115, 32, 101, 113, 117, 97, 108, 32, 116, 111, 46, 46, 46, 32, 37, 100, 10, 10, 0
	string.5 db 73, 39, 109, 32, 115, 108, 101, 101, 112, 105, 110, 103, 32, 102, 111, 114, 32, 49, 32, 115, 101, 99, 111, 110, 100, 33, 0
	string.6 db 73, 39, 109, 32, 97, 119, 97, 107, 101, 32, 110, 111, 119, 33, 10, 0
	string.7 db 109, 121, 32, 111, 116, 104, 101, 114, 32, 102, 117, 110, 99, 32, 97, 108, 119, 97, 121, 115, 32, 114, 101, 116, 117, 114, 110, 115, 32, 37, 100, 63, 63, 63, 10, 0
	string.8 db 105, 110, 110, 101, 114, 32, 102, 117, 110, 99, 116, 105, 111, 110, 32, 114, 101, 116, 117, 114, 110, 115, 32, 39, 37, 115, 39, 46, 46, 46, 10, 0