
; jsr 0xe544

; Taken from: https://www.youtube.com/watch?v=9hLGvLvTs1w

    ldx #0
loop:
    lda message,x
    ; sta 0x0400,x
    jsr 0xffd2
    inx
    cpx #5
    bne loop

    rts

message:
db 65
db 66
db 67
db 65
db 66
db 67
db 0

