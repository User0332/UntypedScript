Generated Assembly Code (unprocessed, note that this assembly will not run properly - `-d unprocessed` is merely a tool to look into compiler internals):
section .text
anonymous.1:
	push ebp
	mov ebp, esp
	sub esp, 4
	
	
	mov eax, [ebp+8]
	push eax
	mov eax, 0
	pop ebx
	cmp ebx, eax
	sete al
	movzx eax, al
	cmp eax, 0
	jne .if.1
	jmp .else.1
	.if.1:
	mov eax, 0
	; <add-later? [check-allocated-bytes]>
	pop ebp
	ret
	jmp .cont.1
	.else.1:
	.cont.1:
	mov eax, 0
	mov [ebp-4], eax
	mov eax, [localonly.arg_offset.NOT_THREAD_SAFE.1]
	mov eax, [ebp+eax+16]
	push eax
	mov eax, string.2
	push eax
	
	lea eax, [_printf]
	; <create-later [localonly-add-to-offset]>
	call eax
	add esp, 8
	; <create-later [localonly-sub-from-offset]>
	
	mov eax, [ebp+8]
	push eax
	mov eax, 1
	pop ebx
	sub ebx, eax
	mov eax, ebx
	push eax
	mov eax, [localonly.arg_offset.NOT_THREAD_SAFE.1]
	mov eax, [ebp+eax+12]
	; <create-later [localonly-add-to-offset]>
	call eax
	add esp, 4
	; <create-later [localonly-sub-from-offset]>
	mov eax, 0
	mov esp, ebp
	pop ebp
	ret
	mov esp, ebp
	pop ebp
	ret
_main:
	push ebp
	mov ebp, esp
	sub esp, 8
	
	mov eax, string.0
	mov [ebp-4], eax
	mov eax, anonymous.1
	mov [ebp-8], eax
	
	mov eax, [ebp-8]
	push eax
	mov eax, string.4
	push eax
	
	lea eax, [_printf]
	call eax
	add esp, 8
	mov eax, string.5
	mov [ebp-4], eax
	mov eax, 3
	push eax
	
	mov eax, [ebp-8]
	call eax
	add esp, 4
	mov eax, string.6
	mov [ebp-4], eax
	mov eax, 1
	push eax
	
	mov eax, [ebp-8]
	call eax
	add esp, 4
	mov eax, 0
	mov esp, ebp
	pop ebp
	ret
	mov esp, ebp
	pop ebp
	ret
