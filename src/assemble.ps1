$name = $args[0]
$asmfile = $name+".asm"
$objfile = $name+".o"

nasm -f win32 -o $objfile $asmfile
gcc -o $name".exe" $objfile

Remove-Item $asmfile
Remove-Item $objfile