$name = $args[0]
$asmfile = $name+".asm"
$objfile = $name+".o"
$linkwith = $args[1..($args.Count-1)] # fix later, is broken

nasm -f win32 -o $objfile $asmfile
gcc -o $name".exe" $objfile $linkwith

Remove-Item $asmfile
Remove-Item $objfile