
extern _printf
extern _strcmp
extern _malloc
extern _Object.AddProperty
extern _Object.HasProperty
extern _Object.AddPropertySafe
extern _Object.DeAllocate
extern _Object.GetProperty
extern _Object.SetProperty
extern _Object.SetPropertySafe
extern _Object.GetPropertySafe
extern _Object.Properties
global _main

section .bss

section .text
anonymous.2:
	push ebp
	mov ebp, esp
	sub esp, 0
	
	mov eax, string.1
	push eax
	mov eax, [ebp+12]
	push eax
	lea eax, [_strcmp]
	call eax
	add esp, 8
	push eax
	mov eax, 0
	pop ebx
	cmp ebx, eax
	sete al
	movzx eax, al
	cmp eax, 0
	jne .if.0
	jmp .else.0
	.if.0:
	mov eax, [ebp+8]
	push eax
	mov eax, 12
	pop ebx
	add ebx, eax
	mov eax, ebx
	pop ebp
	ret
	jmp .cont.0
	.else.0:
	.cont.0:
	pop ebp
	ret
anonymous.5:
	push ebp
	mov ebp, esp
	sub esp, 0
	
	mov eax, string.4
	push eax
	mov eax, [ebp+12]
	push eax
	lea eax, [_strcmp]
	call eax
	add esp, 8
	push eax
	mov eax, 0
	pop ebx
	cmp ebx, eax
	sete al
	movzx eax, al
	cmp eax, 0
	jne .if.3
	jmp .else.3
	.if.3:
	mov eax, [ebp+16]
	push eax
	mov eax, [ebp+8]
	mov eax, [eax]
	push eax
	mov eax, 12
	pop ebx
	add ebx, eax
	mov eax, ebx
	pop DWORD [eax]
	mov eax, 0
	pop ebp
	ret
	jmp .cont.3
	.else.3:
	.cont.3:
	mov eax, [ebp+16]
	push eax
	mov eax, [ebp+12]
	push eax
	mov eax, [ebp+8]
	mov eax, [eax]
	push eax
	lea eax, [_Object.AddProperty]
	call eax
	add esp, 12
	push eax
	mov eax, [ebp+8]
	pop DWORD [eax]
	pop ebp
	ret
_main:
	push ebp
	mov ebp, esp
	sub esp, 12
	
	mov eax, 16
	push eax
	lea eax, [_malloc]
	call eax
	add esp, 4
	mov [ebp-4], eax
	mov eax, anonymous.2
	push eax
	mov eax, [ebp-4]
	push eax
	mov eax, 0
	push eax
	mov eax, 4
	pop ebx
	imul ebx, eax
	mov eax, ebx
	pop ebx
	add ebx, eax
	mov eax, ebx
	pop DWORD [eax]
	mov eax, anonymous.5
	push eax
	mov eax, [ebp-4]
	push eax
	mov eax, 1
	push eax
	mov eax, 4
	pop ebx
	imul ebx, eax
	mov eax, ebx
	pop ebx
	add ebx, eax
	mov eax, ebx
	pop DWORD [eax]
	mov eax, 8
	push eax
	lea eax, [_malloc]
	call eax
	add esp, 4
	mov [ebp-8], eax
	mov eax, string.6
	push eax
	mov eax, [ebp-8]
	push eax
	mov eax, 0
	push eax
	mov eax, 4
	pop ebx
	imul ebx, eax
	mov eax, ebx
	pop ebx
	add ebx, eax
	mov eax, ebx
	pop DWORD [eax]
	mov eax, 0
	push eax
	mov eax, [ebp-8]
	push eax
	mov eax, 1
	push eax
	mov eax, 4
	pop ebx
	imul ebx, eax
	mov eax, ebx
	pop ebx
	add ebx, eax
	mov eax, ebx
	pop DWORD [eax]
	mov eax, [ebp-8]
	push eax
	mov eax, [ebp-4]
	push eax
	mov eax, 2
	push eax
	mov eax, 4
	pop ebx
	imul ebx, eax
	mov eax, ebx
	pop ebx
	add ebx, eax
	mov eax, ebx
	pop DWORD [eax]
	mov eax, string.7
	push eax
	mov eax, [ebp-4]
	push eax
	mov eax, 3
	push eax
	mov eax, 4
	pop ebx
	imul ebx, eax
	mov eax, ebx
	pop ebx
	add ebx, eax
	mov eax, ebx
	pop DWORD [eax]
	mov eax, [ebp-4]
	mov [ebp-4], eax
	mov eax, 25
	push eax
	mov eax, string.8
	push eax
	mov eax, [ebp-4]
	push eax
	lea eax, [_Object.AddProperty]
	call eax
	add esp, 12
	mov [ebp-4], eax
	mov eax, string.9
	push eax
	mov eax, [ebp-4]
	push eax
	call [eax]
	add esp, 8
	mov eax, [eax]
	push eax
	mov eax, string.10
	push eax
	lea eax, [_printf]
	call eax
	add esp, 8
	mov eax, string.11
	push eax
	mov eax, [ebp-4]
	push eax
	call [eax]
	add esp, 8
	mov eax, [eax]
	push eax
	mov eax, string.12
	push eax
	lea eax, [_printf]
	call eax
	add esp, 8
	mov eax, [ebp-4]
	push eax
	lea eax, [_Object.DeAllocate]
	call eax
	add esp, 4
	mov eax, 0
	mov esp, ebp
	pop ebp
	ret
	mov esp, ebp
	pop ebp
	ret

section .data
	string.1 db 110, 97, 109, 101, 0
	string.4 db 110, 97, 109, 101, 0
	string.6 db 110, 97, 109, 101, 0
	string.7 db 74, 97, 99, 107, 0
	string.8 db 97, 103, 101, 0
	string.9 db 110, 97, 109, 101, 0
	string.10 db 110, 97, 109, 101, 32, 61, 32, 37, 115, 10, 0
	string.11 db 97, 103, 101, 0
	string.12 db 97, 103, 101, 32, 61, 32, 37, 100, 10, 0