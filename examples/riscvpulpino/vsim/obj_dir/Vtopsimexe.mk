include Vtopsim.mk
### Executable rules... (from --exe)
VPATH += $(VM_USER_DIR)

jtag_dpi.o: ../jtagdpi/jtag_dpi.c
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(OPT_FAST) -c -o $@ $<
tb.o: tb.cpp
	$(CXX) $(CXXFLAGS) $(CPPFLAGS) $(OPT_FAST) -c -o $@ $<

### Link rules... (from --exe)
Vtopsim:  $(VK_GLOBAL_OBJS) $(VK_USER_OBJS) $(VM_PREFIX)__ALL.a 
	$(LINK) $(LDFLAGS) $^ $(LOADLIBES) $(LDLIBS) -o $@ $(LIBS) $(SC_LIBS) 2>&1 | c++filt


