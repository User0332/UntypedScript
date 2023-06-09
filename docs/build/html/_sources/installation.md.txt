# Installing UntypedScript

In order to install UTSC, or the UntypedScript compiler, you will need the following dependencies:
- [Python (>= 3.9)](https://www.python.org/downloads/)
- [MinGW](https://sourceforge.net/projects/mingw/files/latest/download) or [MinGW w64](https://www.mingw-w64.org/downloads/)
    - Not needed on *nix, `gcc` and `ld` will suffice
- [NASM](https://www.nasm.us/)

Once you've installed all the necessary tools, you can start to install the UntypedScript compiler! It's easy to install using `pip` - just run `pip install untypedscript-utsc` or `python -m pip install untypedscript-utsc`. After installing `untypedscript-utsc`, run the command `utsc-configure` and input the path on your computer to `nasm.exe`, `gcc.exe` and `ld.exe` (these three executables are from the NASM and MinGW installs). After you have your configuration set up, you've successfully installed the UntypedScript compiler and can head over to [Get Started](getstarted.md#get-started).