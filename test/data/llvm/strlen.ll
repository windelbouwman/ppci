; ModuleID = 'strlen.c'
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: nounwind sspstrong uwtable
define i32 @_strlen(i8* %p) #0 {
  %1 = alloca i8*, align 8
  %l = alloca i32, align 4
  store i8* %p, i8** %1, align 8
  store i32 0, i32* %l, align 4
  br label %2

; <label>:2                                       ; preds = %7, %0
  %3 = load i8*, i8** %1, align 8
  %4 = getelementptr inbounds i8, i8* %3, i32 1
  store i8* %4, i8** %1, align 8
  %5 = load i8, i8* %3, align 1
  %6 = icmp ne i8 %5, 0
  br i1 %6, label %7, label %10

; <label>:7                                       ; preds = %2
  %8 = load i32, i32* %l, align 4
  %9 = add i32 %8, 1
  store i32 %9, i32* %l, align 4
  br label %2

; <label>:10                                      ; preds = %2
  %11 = load i32, i32* %l, align 4
  ret i32 %11
}

attributes #0 = { nounwind sspstrong uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"PIC Level", i32 2}
!1 = !{!"clang version 3.8.1 (tags/RELEASE_381/final)"}
