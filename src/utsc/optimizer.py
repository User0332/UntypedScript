#The below assembly optimizer will optimize the assembly code
#rather than the syntax tree. The optimizer will remove redundant
#code like:
#mov eax, 4
#mov [ADDR], eax
#Into:
#mov [ADDR], 4
#The optimizer will also remove inefficient expressions
#that could be optimized like assigning a value to a variable
#in a loop where the variable is never used.
#instead, ecx could just be used as the counter.

from re import match as re_match

class AssemblyOptimizer:
	def __init__(self, asm: str):
		self.asm = asm
		self.optimized = ""
		self.VALID_REGISTERS = (
			"rax", "eax",  "ax", "ah", "al",
			"rbx", "ebx",  "bx", "bh", "bl",
			"rcx", "ecx",  "cx", "ch", "cl",
			"rdx", "edx",  "dx", "dh", "dl",
			"rbp", "ebp",  "bp", "bpl",
			"rsp", "esp",  "sp", "spl",			
			"rsi", "esi",  "si", "sil",			
			"rdi", "edi",  "di", "dil"
		)

	def optimize(self):
		mov_into_eax = False
		mov_into_eax_val = None

		for i, line in enumerate(self.asm.splitlines()):
			line = line.strip()

			if "; no-optimize" in line:
				self.optimized+=line+"\n"
				continue

			match = re_match("mov (.*), 0", line)

			try:
				reg = match.group(1)

				if reg in self.VALID_REGISTERS:
					self.optimized+=f"xor {reg}, {reg}\n"
					continue
			except AttributeError: pass

			if mov_into_eax:
				movinstr = re_match("mov (\[.*\]), eax", line)
				try:
					# here we use DWORD, but in the future, when the 64-bit compiler option is introduced, this needs to be dependent 
					# on that option rather than just DWORD (e.g. it could be QWORD with 64-bit types)
					dest = movinstr.group(1)
					
					if ('[' in dest) and ('[' in mov_into_eax_val):
						raise AttributeError() # nasm will not accept two dereferenced addresses like this
					
					self.optimized+=f"mov DWORD {dest}, {mov_into_eax_val}\n"
					mov_into_eax = False
				except AttributeError:
					if line == "push eax":
						self.optimized+=f"push DWORD {mov_into_eax_val}\n"
						mov_into_eax = False
						continue
					mov_into_eax = False
					self.optimized+=f"mov eax, {mov_into_eax_val}\n{line}\n"

				continue

			if line.startswith("mov eax, "):
				mov_into_eax = True
				mov_into_eax_val = line.removeprefix("mov eax, ")
				continue

			self.optimized+=line+"\n"

		return self.optimized
