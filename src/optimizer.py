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

from re import finditer as re_finditer

class AssemblyOptimizer:
	def __init__(self, asm: str):
		self.asm = asm
		self.optimized = ""


	def optimize(self):
		mov_into_eax = False
		mov_into_eax_val = None

		for i, line in enumerate(self.asm.splitlines()):
			line = line.strip()
			
			match = re_finditer("mov (.*), 0", line)
			if match:
				reg = next(match).group(1)

				line = f"xor {reg}, {reg}"
				

			if line.startswith("mov eax, "):
				mov_into_eax = True
				mov_into_eax_val = line.removeprefix("mov eax, ")
			if mov_into_eax:
				movinstr = re_finditer("mov (\[.*\]), eax", line)
				if movinstr:
					movinstr = next(movinstr)
					self.optimized+=f"mov {movinstr.group(1)}, {mov_into_eax_val}"
				else:
					mov_into_eax = False
					self.optimized+=line+"\n"
			else:
				self.optimized+=line+"\n"


		return self.optimized
