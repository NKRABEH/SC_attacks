# Differential power analysis of a DES crypto-processor

## General description

This folder contains code which retrieve a DES last round key from a set of power traces. The target implementation is the hardware DES crypto-processor which architecture is depicted in the following figure: 
![DES architecture]

As can be seen from the DES architecture a full encryption takes 32 cycles (in our case the secret key is input once and then never changes):

* 8 cycles to input the message to process, one byte at a time, in the IO register
* 16 cycles to compute the 16 rounds of DES, one round per cycle,
* 8 cycles to output the result, one byte at a time, from the IO register.


The DES engine runs at 32 MHz, delivering a processing power of up to 2 millions of DES encryptions per second (only one million of DES encryptions per second for this lab where I/O and processing are not parallelized).

Using this architecture, 10000 different 64 bits messages were encrypted with the same known secret key. During the encryptions the power traces could be recorded by sampling the voltage drop across a small resistor inserted between the power supply and the crypto-processor.
Each power trace should be recorded several times and averaged in order to increase the voltage resolution.
for the purpose of this lab, a data simulator generates these traces as well as input plain texts and the produced cipher texts.
The sampling frequency for the samples is 20 Gs/s, but the power traces have been down-sampled by a factor of 25. Despite this quality loss it is indeed still perfectly feasible to recover the secret key. And because the traces only contain 800 points each (32 clock periods times 25 points per clock period), the attack runs much faster than with the original time resolution (20000 points per power trace). 


### Acquisitions

The power traces, plaintexts, ciphertexts and secret key are available in the binary `pa.hws` file. In the following we use the term _acquisition_ to designate a record in this file. The file contains some global parameters: number of acquisitions in the file (10000), number of samples per power trace (800), 64 bits secret key and 10000 acquisitions, each made of a 64 bits plain text, the corresponding 64 bits cipher text and a power trace. Power traces are 800 samples long and span over the 32 clock periods (25 samples per clock period) of a DES operation. The following figure represents such a power trace with the time as horizontal axis and the power (instantaneous voltage) as vertical axis:

![A power trace]

Software routines are provided to read this binary file.

The `pa.key` text file contains the 64-bits DES secret key, its 56-bits version (without the parity bits), the 16 corresponding 48-bits round keys and, for each round key, the eight 6-bits sub-keys. It also contains some information about the power traces.

### Attack program
The attack program takes 2 command line parameters: the name of a file containing acquisitions and a number of acquisitions to use. The acquisitions we use in this lab are stored in `pa.hws`. So, when running the program, you will provide this name as first parameter. The number of acquisitions to use (second parameter) must be between 1 and 10000 because the acquisitions file contains 10000 acquisitions only.

When run with these 2 parameters the program will:
* First checks the DES software library for correctness.
* Read the 2 command line parameters.
* Load the specified number of acquisitions in a dedicated data structure (`tr_context ctx`).
* Compute the average power trace, store it in a data file named `average.dat` and also create a command file named `average.cmd` for the `gnuplot` utility .
* We Attack the given number of acquisitions with the scenario described in P. Kocher's paper on DPA [1] : assuming we know 6 bits of the 48 bits last round key (64 different possibilities), we can use the cipher text of an acquisition to compute the value of one bit of `L15`. By default (but this can be changed), the target bit is the leftmost bit in `L15` (numbered 1 according DES standard numbering convention). For each of the 64 candidate sub-keys we can do the same, leading to 64 values of the target bit. Let `d[i,g]` (scalar) be the computed value of the target bit for acquisition `i` and candidate sub-key value `g`. Let `T[i]` (vector) be the power trace of acquisition `i`. The algorithm of the attack is the following:

```
for g in 0 to 63 { // For all guesses on the 6-bits sub-key
  T0[g] <- {0,0,...,0}; // Initialize the zero-set trace
  T1[g] <- {0,0,...,0}; // Initialize the one-set trace
} // End for all guesses
for i in 0 to n-1 {  // For all acquisitions
  for g in 0 to 63 { // For all guesses on the 6-bits sub-key
    compute d[i,g]   // Compute target bit
    if d[i,g] = 0 {  // If target bit is zero for this guess
      T0[g] <- T0[g] + T[i]; // Accumulate power trace to zero-set
    }
    else { // Else, if target bit is one for this guess
      T1[g] <- T1[g] + T[i]; // Accumulate power trace to one-set
    }
  } // End for all guesses
} // End for all acquisitions
for g in 0 to 63 { // For all guesses on the 6-bits sub-key
  DPA[g] <- average (T1[g]) - average (T0[g]); // Compute DPA trace
  max[g] <- maximum (DPA[g]); // Search maximum of DPA trace
} // End for all guesses
best_guess <- argmax (max);  // Index of largest value in max array
return best_guess;
```

* The program stores the 64 computed DPA traces into a data file named `dpa.dat` and create a `gnuplot` command file named `dpa.cmd`. It also prints a summary indicating the index of the target bit, the index of the corresponding SBox (also index of the corresponding 6-bits sub-key), the best guess for the 6-bits sub-key, the amplitude of the highest peak in all DPA traces, the index of this maximum in the trace (that is, the time of the event that caused this peak).
* Finally, the program prints the last round key. It then frees the allocated memory and exits.

All printed messages are sent to the standard error (`stderr`) or one of the output files for `gnuplot`. The only message that is sent to the standard output (`stdout`) is the 48-bits last round key, in hexadecimal form.

Run the example program on the whole set of acquisitions:
```bash
$  ./pa.py pa.hws 10000
Average power trace stored in file 'average.dat'. In order to plot it, type:
$ gnuplot -persist average.cmd
Target bit: 1
Target SBox: 4
Best guess: 54 (0x36)
Maximum of DPA trace: 6.541252e-03
Index of maximum in DPA trace: 105
DPA traces stored in file 'dpa.dat'. In order to plot them, type:
$ gnuplot -persist dpa.cmd
Last round key (hex):
0x0123456789ab
```

To display the generated average power trace:

```bash
$ gnuplot -persist average.cmd
```
To displaythe DPA traces:

```bash
$ gnuplot -persist dpa.cmd
```

The red trace is the one with the highest peak, the one corresponding to the found best guess. All the other 63 DPA traces are plotted in blue. 
Try to understand this example program and play with it. Note that it optionally takes a third parameter to specify the index of the target bit in `L15` (1 to 32, as in the DES standard, default: 1). So, running:

```bash
$  ./pa.py pa.hws 10000
```

is just like running:

```bash
$ ./pa.py pa.hws 10000 1
```

Here is an example of what you could try to do with this third optional parameter: use the provided DPA program example 32 times on the 32 different target bits. Have a look at some DPA traces with `gnuplot`, if you wish. For each of the 32 acquisitions fill a line in the [provided table]. Note: the line corresponding to the example above is already filled.

Remark:  it takes some time to run all these 32 experiments (especially in python).


For verification, we can check that the printed 48-bits last round key is the same as in `pa.key`.


## references
[1] Differential Power Analysis (Paul Kocher, Joshua Jaffe, and Benjamin Jun): https://42xtjqm0qj0382ac91ye9exr-wpengine.netdna-ssl.com/wp-content/uploads/2015/08/DPA.pdf \
[2] DES python library: http://soc.eurecom.fr/HWSec/doc/pa/python/des.html \
[3] traces python library: http://soc.eurecom.fr/HWSec/doc/pa/python/traces.html \
[4] tr_pcc python library: http://soc.eurecom.fr/HWSec/doc/pa/python/tr_pcc.html \
[5] km python library: http://soc.eurecom.fr/HWSec/doc/pa/python/km.html \

[A power trace]: ../doc/trace.png

[DES architecture]: ../doc/des_architecture.png

[provided table]: ../doc/des_pa_table.pdf
<!-- vim: set tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab textwidth=0: -->
