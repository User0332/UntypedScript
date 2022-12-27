#!/usr/bin/bash


# NOT TESTED YET
$name = $1
$asmfile = $name+".asm"
$objfile = $name+".o"

nasm -f elf32 -o $objfile $asmfile
gcc -o $name".exe" $objfile

rm $asmfile
rm $objfile
