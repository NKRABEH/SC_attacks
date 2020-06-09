<!-- MASTER-ONLY: DO NOT MODIFY THIS FILE-->

# Timing attack against a DES software implementation

## General description

In this attack I exploit a flaw in a DES software implementation which computation time depends on the input messages and on the secret key: its P permutation was implemented vulnerable to timing attacks. The pseudo-code of his implementation of the P permutation is the following:

```
// Permutation table. Input bit #16 is output bit #1 and
// input bit #25 is output  bit #32.
p_table = {16,  7, 20, 21,
           29, 12, 28, 17,
            1, 15, 23, 26,
            5, 18, 31, 10,
            2,  8, 24, 14,
           32, 27,  3,  9,
           19, 13, 30,  6,
           22, 11,  4, 25};

p_permutation(val) {
  res = 0;                    // Initialize the 32 bits output result to all zeros
  for i in 1 to 32 {          // For all input bits #i (32 of them)
    if get_bit(i, val) == 1   // If input bit #i is set
      for j in 1 to 32        // For all 32 output bits #j (32 of them)
        if p_table[j] == i    // If output bits #j is input bit #i
          k = j;              // Remember output bit index
        endif
      endfor                  // output bit #k corresponds to input bit #i
      set_bit(k, res);        // Set bit #k of result
    endif
  endfor
  return res;                 // Return result
}
```



## Directions


### Build all executables

```bash
$ cd PATH_TO/SC_attack/timingAttack
$ make all
```

### Acquisition phase

Run the acquisition phase:

```bash
$ ./ta_acquisition 100000
100%
Experiments stored in: ta.dat
Secret key stored in:  ta.key
Last round key (hex):
0x79629dac3cf0
``` 

This will randomly draw a 64-bits DES secret key, 100000 random 64-bits plaintexts and encipher them using the flawed DES software implementation. Each enciphering will also be accurately timed using the hardware timer of your computer. Be patient, the more acquisitions you request, the longer it takes. Two files will be generated:
* `ta.key` containing the 64-bits DES secret key, its 56-bits version (without the parity bits), the 16 corresponding 48-bits round keys and, for each round key, the eight 6-bits subkeys.
* `ta.dat` containing the 100000 ciphertexts and timing measurements.

Note: the 48-bits last round key is printed on the standard output (`stdout`), all other printed messages are sent to the standard error (`stderr`).

Note: you can also chose the secret key with:

```bash
$ ./ta_acquisition 100000 0x0123456789abcdef
```

where `0x0123456789abcdef` is the 64-bits DES secret key you want to use, in hexadecimal form.

Note: if for any reason you cannot run `ta_acquisition`, use the provided `ta.dat.example` and `ta.key.example` files, instead.

Let us look at the few first lines of `ta.dat`:

```bash
$ head -4 ta.dat
0x743bf72164b3b7bc 80017.500000
0x454ef17782801ac6 76999.000000
0x9800a7b2214293ed 74463.900000
0x1814764423289ec1 78772.500000
```

Each line is an acquisition corresponding to one of the 100000 random plaintexts. The first field on the line is the 64 bits ciphertext returned by the DES engine, in hexadecimal form. With the numbering convention of the DES standard, the leftmost character (7 in the first acquisition of the above example) corresponds to bits 1 to 4. The following one (4) corresponds to bits 5 to 8 and so on until the rightmost (c) which corresponds to bits 61 to 64. In the first acquisition of the above example, bit number 6 is set while bit number 8 is unset.The second field is the timing measurement.

### Attack phase

The acquisition phase is over, it is now time to design a timing attack. Use the `ta.key` file for verification. The provided example application:
* takes two arguments: the name of a data file and a number of acquisitions to use,
* reads the specified number of acquisitions from the data file,
* stores the ciphertexts and timing measurements in two arrays named `ct` and `t`,
* assumes that the last round key is `0x0123456789ab`, and based on this, computes the 4-bits output of SBox #1 in the last round of the last acquisition, and prints its Hamming weight,
* computes and prints the average value of the timing measurements of all acquisitions and, finally,
* prints the assumed `0x0123456789ab` last round key in hexadecimal format.

All printed messages are sent to the standard error (`stderr`). The only message that is sent to the standard output (`stdout`) is the 48-bits last round key, in hexadecimal form.

The example application uses some functions of the provided software libraries. To see the complete list of what these libraries offer, look at their documentation (see the [Some useful material](#some-useful-material) section). To compile and run the example application (C version) just type:

```bash
$ make ta
$ ./ta ta.dat 100000
Hamming weight: 1
Average timing: 169490.540600
Last round key (hex):
0x0123456789ab
```

vered the last round key, try to reduce the number of acquisitions you are using: the less acquisitions the more practical your attack.

### Countermeasure

Last, but not least, design a countermeasure by rewriting the P permutation function. The `p.c` file contains the C (no python version, sorry) source code of the function. Edit it and fix the flaw, save the file and compile the new version of the `ta_acquisition` application:

```bash
$ make all
```

This will compile the acquisition application with your implementation of the P permutation function. Fix the errors if any.

Run again the acquisition phase:

```bash
$ ./ta_acquisition 100000
```

This will first check the functional correctness of the modified DES implementation. Fix the errors if any until the application runs fine and creates a new `ta.dat` file containing 100000 acquisitions. Try to attack with these acquisitions and see whether it still works... Do you think your implementation is really protected against timing attacks? Explain. If you are not convinced that your implementation is 100% safe, explain what we could do to improve it.


## references

* The [DES standard]
* [Timing Attacks on Implementations of Diffie-Hellman, RSA, DSS, and Other Systems (Paul Kocher, CRYPTO'96)]
* For the C language version:
    * [The **des** library, dedicated to the Data Encryption Standard (DES)][DES C library]
    * [The **pcc** library, dedicated to the computation of Pearson Correlation Coefficients (PCC)][pcc C library]
    * [The **km** library, to manage the partial knowledge about a DES (Data Encryption Standard) secret key][km C library]

[DES C library]: http://soc.eurecom.fr/HWSec/doc/ta/C/des_8h.html
[pcc C library]: http://soc.eurecom.fr/HWSec/doc/ta/C/pcc_8h.html
[km C library]: http://soc.eurecom.fr/HWSec/doc/ta/C/km_8h.html 
[initial setup]: https://gitlab.eurecom.fr/renaud.pacalet/hwsec#gitlab-and-git-set-up
[DES standard]: ../doc/des.pdf
[Timing Attacks on Implementations of Diffie-Hellman, RSA, DSS, and Other Systems (Paul Kocher, CRYPTO'96)]: http://www.cryptography.com/resources/whitepapers/TimingAttacks.pdf
[hwsec project]: https://gitlab.eurecom.fr/renaud.pacalet/hwsec
<!-- vim: set tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab textwidth=0: -->
