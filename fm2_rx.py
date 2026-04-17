from gnuradio import gr, blocks, analog, filter
from gnuradio import network
from gnuradio.filter import firdes
from gnuradio.fft import window
import osmosdr
import time

class FMReceiver(gr.top_block):
    def __init__(self, freq=104.8e6, rf_gain=40):
        gr.top_block.__init__(self, "FM Receiver")

        samp_rate = 2.048e6

        self.src = osmosdr.source(args="numchan=1")
        self.src.set_sample_rate(samp_rate)
        self.src.set_center_freq(freq)
        self.src.set_gain_mode(False)
        self.src.set_gain(rf_gain)

        self.lpf = filter.fir_filter_ccf(
            10,
            firdes.low_pass(
                1.0,
                samp_rate,
                100e3,
                25e3,
                window.WIN_HAMMING,
                6.76
            )
        )

        self.wbfm = analog.wfm_rcv(
            quad_rate=204800,
            audio_decimation=4
        )

        self.resampler = filter.rational_resampler_fff(
            interpolation=240,
            decimation=256
        )

        self.volume = blocks.multiply_const_ff(2.0)
        self.float_to_short = blocks.float_to_short(1, 32767)

        self.udp = network.udp_sink(
   	 2,
   	 1,
   	 "127.0.0.1",
   	 1235,
   	 0,
   	 1472,
   	 True
	)
        self.connect(
            self.src,
            self.lpf,
            self.wbfm,
            self.resampler,
            self.volume,
            self.float_to_short,
	    self.udp
        )

if __name__ == "__main__":
    tb = FMReceiver( # замени на IP твоего ПК
        freq=104.8e6,
        rf_gain=40
    )
    tb.start()
import time

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    tb.stop()
    tb.wait()
