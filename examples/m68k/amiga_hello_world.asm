
; Roughly taken from:
; https://github.com/Sakura-IT/Amiga-programming-examples/blob/master/ASM/HelloWorld/helloworld.s

; See also:
; http://amigadev.elowar.com/read/ADCD_2.1/Includes_and_Autodocs_2._guide/node0367.html
; open library
lea dosname, a1
moveq #36, d0  ; version 36 = Kick 2.0
moveal (4).W, a6
jsr (-552, a6)  ; -552 = OpenLibrary

lea txt, a6  ; load string name
movel a6, d1  ; d1 = string to print
moveal d0, a6  ; Move dosbase to a6
jsr (-948, a6) ; -948 = PutStr

; close library
moveal a6, a1  ; Library to close
moveal (4).W, a6
jsr (-414, a6)  ; -414 = CloseLibrary

; clr.l d0
moveq #0, d0
rts

dosname: 
; TODO: ds "dos.library", 0

db 0x64
db 0x6f
db 0x73
db 0x2e
db 0x6c
db 0x69
db 0x62
db 0x72
db 0x61
db 0x72
db 0x79
db 0

txt:
; "Hoi!", 0
db 0x48
db 0x6f
db 0x69
db 0x21
db 0

