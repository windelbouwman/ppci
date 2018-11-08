
; Roughly taken from:
; https://github.com/Sakura-IT/Amiga-programming-examples/blob/master/ASM/HelloWorld/helloworld.s

; See also:
; http://amigadev.elowar.com/read/ADCD_2.1/Includes_and_Autodocs_2._guide/node0367.html
; open library
; lea dosname, a1
; movel #36, d0  ; version 36 = Kick 2.0
moveaw #4, a6
jsr (-552, a6)  ; -552 = OpenLibrary


moveal d0, a6  ; Move dosbase to a6
jsr (-948, a6) ; -948 = PutStr

; close library
moveal a6, a1  ; Library to close
moveaw #4, a6
jsr (-414, a6)  ; -414 = CloseLibrary

; clr.l d0
movew #0, d0
rts

; dosname: ds "dos.library", 0
