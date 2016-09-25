; ModuleID = 'strlen.c'
target datalayout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

; Function Attrs: nounwind readonly sspstrong uwtable
define i64 @strlen(i8* nonnull %str) #0 {
  %1 = alloca i8*, align 8
  %s = alloca i8*, align 8
  store i8* %str, i8** %1, align 8
  %2 = load i8*, i8** %1, align 8
  store i8* %2, i8** %s, align 8
  br label %3

; <label>:3                                       ; preds = %8, %0
  %4 = load i8*, i8** %s, align 8
  %5 = load i8, i8* %4, align 1
  %6 = icmp ne i8 %5, 0
  br i1 %6, label %7, label %11

; <label>:7                                       ; preds = %3
  br label %8

; <label>:8                                       ; preds = %7
  %9 = load i8*, i8** %s, align 8
  %10 = getelementptr inbounds i8, i8* %9, i32 1
  store i8* %10, i8** %s, align 8
  br label %3

; <label>:11                                      ; preds = %3
  %12 = load i8*, i8** %s, align 8
  %13 = load i8*, i8** %1, align 8
  %14 = ptrtoint i8* %12 to i64
  %15 = ptrtoint i8* %13 to i64
  %16 = sub i64 %14, %15
  ret i64 %16
}

attributes #0 = { nounwind readonly sspstrong uwtable "disable-tail-calls"="false" "less-precise-fpmad"="false" "no-frame-pointer-elim"="true" "no-frame-pointer-elim-non-leaf" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+fxsr,+mmx,+sse,+sse2" "unsafe-fp-math"="false" "use-soft-float"="false" }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"PIC Level", i32 2}
!1 = !{!"clang version 3.8.1 (tags/RELEASE_381/final)"}
