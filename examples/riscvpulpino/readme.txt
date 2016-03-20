1. generate l2_stim.slm and tcdm_bank0.slm by running mkfirmpulpino.py
For the simulation verilator(www.veripool.org) needs to be installed. To
compile the pulpino-sources with verilator:
2. cd vsim
3. ./verilate.sh
5. cp ob_dir/Vpulpino_top ..
6. cd ..
7. ./Vpulpino_top
