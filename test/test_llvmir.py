import unittest
import io
from ppci.lang.llvmir import LlvmIrFrontend


class LlvmIrFrontendTestCase(unittest.TestCase):
    def test_prog1(self):
        f = io.StringIO(PROG1)
        LlvmIrFrontend().compile(f)

    def test_prog2(self):
        f = io.StringIO(PROG2)
        # LlvmIrFrontend().compile(f)


PROG1 = """
define i32 @square_unsigned(i32 %a) {
  %1 = mul i32 %a, %a
  ret i32 %1
}
"""

PROG2 = """
define void @autogen_SD0(i8*, i32*, i64*, i32, i64, i8) {
BB:
  %A4 = alloca <8 x double>
  %A3 = alloca <2 x i16>
  %A2 = alloca <4 x i8>
  %A1 = alloca <16 x i1>
  %A = alloca <16 x i1>
  %L = load <16 x i1>, <16 x i1>* %A
  store i8 %5, i8* %0
  %E = extractelement <2 x i8> zeroinitializer, i32 0
  %Shuff = shufflevector <4 x i32> zeroinitializer, <4 x i32> zeroinitializer, <4 x i32> <i32 undef, i32 7, i32 1, i32 undef>
  %I = insertelement <1 x i8> zeroinitializer, i8 21, i32 0
  %B = fmul double 0x18DF23FE11DD527C, 0xAE97BFB633957A34
  %Se = sext i8 77 to i16
  %Sl = select i1 true, <8 x i1> zeroinitializer, <8 x i1> zeroinitializer
  %Cmp = icmp ugt i16 18761, %Se
  br label %CF78

CF78:                                             ; preds = %CF78, %BB
  %L5 = load i8, i8* %0
  store i8 21, i8* %0
  %E6 = extractelement <2 x i16> zeroinitializer, i32 0
  %Shuff7 = shufflevector <2 x i8> zeroinitializer, <2 x i8> zeroinitializer, <2 x i32> <i32 undef, i32 3>
  %I8 = insertelement <4 x i32> zeroinitializer, i32 32529, i32 3
  %B9 = sub i64 %4, 251161
  %Tr = trunc <4 x i32> %I8 to <4 x i16>
  %Sl10 = select i1 %Cmp, <2 x i16>* %A3, <2 x i16>* %A3
  %Cmp11 = icmp ne <1 x i8> zeroinitializer, zeroinitializer
  %L12 = load <2 x i16>, <2 x i16>* %Sl10
  store <2 x i16> %L12, <2 x i16>* %Sl10
  %E13 = extractelement <2 x i64> zeroinitializer, i32 1
  %Shuff14 = shufflevector <4 x i32> zeroinitializer, <4 x i32> %Shuff, <4 x i32> <i32 2, i32 undef, i32 6, i32 0>
  %I15 = insertelement <4 x i32> zeroinitializer, i32 %3, i32 0
  %B16 = and i8 %E, 21
  %FC = uitofp <4 x i32> %I15 to <4 x double>
  %Sl17 = select i1 true, i16 -1979, i16 16293
  %Cmp18 = fcmp ueq double 0xAE97BFB633957A34, 0x99ABD3CAB0A9A048
  br i1 %Cmp18, label %CF78, label %CF80

CF80:                                             ; preds = %CF78
  %L19 = load <2 x i16>, <2 x i16>* %Sl10
  store <2 x i16> zeroinitializer, <2 x i16>* %Sl10
  %E20 = extractelement <8 x i1> %Sl, i32 1
  br label %CF

CF:                                               ; preds = %CF, %CF85, %CF86, %CF82, %CF80
  %Shuff21 = shufflevector <8 x i32> zeroinitializer, <8 x i32> zeroinitializer, <8 x i32> <i32 undef, i32 14, i32 0, i32 2, i32 4, i32 6, i32 8, i32 10>
  %I22 = insertelement <16 x i1> zeroinitializer, i1 true, i32 14
  %B23 = mul <1 x i8> %I, zeroinitializer
  %FC24 = fptoui <4 x double> %FC to <4 x i16>
  %Sl25 = select i1 true, i8 %E, i8 %B16
  %Cmp26 = icmp ule i32 0, 132849
  br i1 %Cmp26, label %CF, label %CF85

CF85:                                             ; preds = %CF
  %L27 = load i8, i8* %0
  store <2 x i16> %L12, <2 x i16>* %Sl10
  %E28 = extractelement <2 x i64> zeroinitializer, i32 1
  %Shuff29 = shufflevector <4 x i64> zeroinitializer, <4 x i64> zeroinitializer, <4 x i32> <i32 6, i32 undef, i32 2, i32 4>
  %I30 = insertelement <8 x i32> %Shuff21, i32 132849, i32 0
  %B31 = and i8 77, 21
  %Tr32 = trunc <4 x i32> %I8 to <4 x i16>
  %Sl33 = select i1 true, i8 %B31, i8 %5
  %Cmp34 = icmp ule <2 x i16> %L19, %L12
  %L35 = load <2 x i16>, <2 x i16>* %Sl10
  store i8 %L5, i8* %0
  %E36 = extractelement <2 x i1> %Cmp34, i32 0
  br i1 %E36, label %CF, label %CF84

CF84:                                             ; preds = %CF84, %CF85
  %Shuff37 = shufflevector <16 x i1> %I22, <16 x i1> zeroinitializer, <16 x i32> <i32 7, i32 undef, i32 undef, i32 undef, i32 15, i32 17, i32 undef, i32 21, i32 23, i32 25, i32 27, i32 undef, i32 31, i32 1, i32 3, i32 5>
  %I38 = insertelement <4 x double> %FC, double 0xAE97BFB633957A34, i32 1
  %FC39 = sitofp i8 %L5 to double
  %Sl40 = select i1 true, <16 x i1> %I22, <16 x i1> %I22
  %Cmp41 = icmp uge i8 %Sl25, 21
  br i1 %Cmp41, label %CF84, label %CF86

CF86:                                             ; preds = %CF84
  %L42 = load i8, i8* %0
  store <2 x i16> %L12, <2 x i16>* %Sl10
  %E43 = extractelement <16 x i1> %Shuff37, i32 11
  br i1 %E43, label %CF, label %CF81

CF81:                                             ; preds = %CF81, %CF83, %CF86
  %Shuff44 = shufflevector <4 x i32> zeroinitializer, <4 x i32> zeroinitializer, <4 x i32> <i32 6, i32 0, i32 2, i32 undef>
  %I45 = insertelement <8 x i1> %Sl, i1 true, i32 0
  %B46 = srem <1 x i8> %I, %B23
  %Tr47 = fptrunc double %FC39 to float
  %Sl48 = select i1 %E43, <8 x i1> %I45, <8 x i1> zeroinitializer
  %Cmp49 = icmp eq i64 251161, %E28
  br i1 %Cmp49, label %CF81, label %CF83

CF83:                                             ; preds = %CF81
  %L50 = load <2 x i16>, <2 x i16>* %Sl10
  store i8 21, i8* %0
  %E51 = extractelement <16 x i1> zeroinitializer, i32 10
  br i1 %E51, label %CF81, label %CF82

CF82:                                             ; preds = %CF83
  %Shuff52 = shufflevector <8 x i1> %Sl48, <8 x i1> %I45, <8 x i32> <i32 13, i32 15, i32 1, i32 3, i32 5, i32 undef, i32 9, i32 11>
  %I53 = insertelement <4 x i32> zeroinitializer, i32 0, i32 3
  %FC54 = uitofp <2 x i16> zeroinitializer to <2 x float>
  %Sl55 = select i1 %Cmp26, <4 x i16> %Tr32, <4 x i16> %Tr32
  %Cmp56 = icmp ugt <2 x i16> %L19, zeroinitializer
  %L57 = load <2 x i16>, <2 x i16>* %Sl10
  store i8 %B16, i8* %0
  %E58 = extractelement <2 x i8> %Shuff7, i32 0
  %Shuff59 = shufflevector <8 x i32> zeroinitializer, <8 x i32> %Shuff21, <8 x i32> <i32 7, i32 9, i32 11, i32 13, i32 15, i32 1, i32 3, i32 5>
  %I60 = insertelement <4 x i32> zeroinitializer, i32 %3, i32 1
  %ZE = zext i8 %B31 to i64
  %Sl61 = select i1 %Cmp, i64 %ZE, i64 %ZE
  %Cmp62 = icmp slt <8 x i32> zeroinitializer, zeroinitializer
  %L63 = load <2 x i16>, <2 x i16>* %Sl10
  store i8 %L5, i8* %0
  %E64 = extractelement <4 x i32> zeroinitializer, i32 2
  %Shuff65 = shufflevector <4 x i32> %Shuff, <4 x i32> %I8, <4 x i32> <i32 5, i32 undef, i32 1, i32 undef>
  %I66 = insertelement <16 x i32> zeroinitializer, i32 %E64, i32 7
  %B67 = shl <4 x i16> %FC24, zeroinitializer
  %Se68 = sext i32 132849 to i64
  %Sl69 = select i1 %Cmp18, <8 x i32> %Shuff59, <8 x i32> %Shuff21
  %Cmp70 = icmp sgt i1 %Cmp26, %Cmp18
  br i1 %Cmp70, label %CF, label %CF79

CF79:                                             ; preds = %CF82
  %L71 = load i8, i8* %0
  store i8 %B31, i8* %0
  %E72 = extractelement <4 x i32> zeroinitializer, i32 2
  %Shuff73 = shufflevector <16 x i1> %Sl40, <16 x i1> zeroinitializer, <16 x i32> <i32 13, i32 15, i32 17, i32 undef, i32 21, i32 23, i32 25, i32 27, i32 29, i32 undef, i32 1, i32 3, i32 5, i32 7, i32 9, i32 11>
  %I74 = insertelement <2 x i1> %Cmp56, i1 true, i32 1
  %ZE75 = zext i1 %E20 to i64
  %Sl76 = select i1 true, double 0x99ABD3CAB0A9A048, double %FC39
  %Cmp77 = icmp slt <8 x i32> zeroinitializer, %Shuff59
  store i8 77, i8* %0
  store i8 21, i8* %0
  store <2 x i16> %L12, <2 x i16>* %Sl10
  store i8 %L71, i8* %0
  store i8 21, i8* %0
  ret void
}
"""
