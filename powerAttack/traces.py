#!/usr/bin/env python2

# MASTER-ONLY: DO NOT MODIFY THIS FILE

"""The traces library, a software library dedicated to processing of power
traces in relation with the Data Encryption Standard (DES).

:Date: 2009-07-29
:Authors:
    - Renaud Pacalet, renaud.pacalet@telecom-paristech.fr

Traces are one dimension arrays of floating point numbers. They are stored in
a binary file along with some parameters and their corresponding 64 bits (8
bytes) plaintexts and ciphertexts. The format of the trace files is the
following:

1. "HWSec" (a 5 bytes magic number)
2. N, the number of traces in the file (a 4 bytes unsigned integer)
3. L, the number of points per trace (a 4 bytes unsigned integer)
4. K, the 64 bits secret key (a 8 bytes unsigned integer)
5. N * (8 + 8 + L * 4) bytes corresponding to the N traces. The 8 bytes of
   the plaintext come first, then the 8 bytes of the cycphertext and the L
   floating point numbers (L * 4 bytes) of the trace.

A trace file containing 50 traces, 100 points each will thus be 20813 bytes
long: 5 + 4 + 4 + 50 * (8 + 8 + 100 * 4).

Reading a trace file is done by instantiating a `trContext` object::

import traces
...
ctx = traces.trContext ("MyTraceFile.hws", 1000)

where "MyTraceFile.hws" is a regular trace file in HWSec format and 1000 the
maximum number of traces to read from it. Once initialized, the context
contains every useful information:

1. number of traces in context
2. number of points per trace
3. the secret key
4. the plaintexts
5. ciphertexts
6. power traces

Attention
=========

1. Most functions of the traces library check their input parameters and
   issue warnings or errors when they carry invalid values. Warnings are
   printed on the standard error output. Errors are also printed on the
   standard error output and the program exits with a -1 exit status.
2. The traces library uses a single data type to represent all the data of
   the DES standard: **uint64_t**. It is a 64 bits unsigned integer.
3. DES data are always right aligned: when the data width is less than 64
   bits, the meaningful bits are always the rightmost bits of the
   **uint64_t**.

"""

import struct

HWSECMAGICNUMBER = "HWSec"

class trContext:
    """The data structure used to manage a set of traces
    
    Attributes:
        n (int): Number of traces in the context
        l (int): Number of points per trace
        k (long): Secret key
        p (List[long]): Plaintexts
        c (List[long]): Ciphertexts
        t (List[List[float]]): Power traces

    """

    def __init__ (self, filename, max):
        """Reads the trace file `filename` and initializes the context.

        Args:
            filename (str): Name of the trace file in HWSec format
            max (int): Maximum number of traces to read from the file (read all traces if 0)

        """

        if not isinstance (max, int) or max < 0:
            raise ValueError('Invalid maximum number of traces: ' + str(max))

        with open(str(filename), 'rb') as f:

            header = f.read (len(HWSECMAGICNUMBER) + 4 + 4 + 8)
            if len(header)  != len(HWSECMAGICNUMBER) + 4 + 4 + 8:
                raise ValueError ('wrong header; is this a real HWSec trace file?')

            magic, self.n, self.l, self.k = struct.unpack ("<" + str(len(HWSECMAGICNUMBER)) + "siiQ", header)
            if magic != HWSECMAGICNUMBER:
                raise ValueError ('wrong magic number; is this a real HWSec trace file?')

            if max == 0:
                max = self.n
            elif self.n >= max:
                self.n = max
            else:
                raise ValueError ('not enough traces in trace file (%d < %d)' % (self.n, max))

            self.t = []
            self.c = []
            self.p = []
            for i in range (self.n):
                tr = f.read (8 + 8 + 4 * self.l)
                if len(tr) != 8 + 8 + 4 * self.l:
                    raise ValueError ('cannot read trace %d; is this a real HWSec trace file?' % i)

                l = struct.unpack ("<QQ" + str(self.l) + "f", tr)
                self.p.append (l[0])
                self.c.append (l[1])
                self.t.append (list(l[2:]))

    def trim (self, first_index, length):
        """Trim all the traces of the context, keeping only `length`
        points, starting from point number `first_index`

        Args:
            first_index (int): The index of first point to keep
            length (int): The number of points to keep

        """

        if not isinstance (first_index, int) or not isinstance (length, int):
            raise TypeError('parameters first_index and length should be numbers')

        first = first_index % self.l
        if length < 0 or first + length > self.l:
            raise ValueError('Invalid parameters value: first_index=%d, length=%d (traces length=%d)' % (first_index, length, self.l))

        self.t = [tt[first:first+length] for tt in self.t]
        self.l = length

    def select (self, first_trace, n):
        """Selects `n` traces of the context, starting from trace number `first_trace`,
        and discards the others

        Args:
            first_trace (int): Index of first trace to keep.
            n (int): Number of traces to keep.

        """

        if not isinstance (first_trace, int) or not isinstance (n, int):
            raise TypeError('parameters first_trace and n should be numbers')

        first = first_trace % self.n
        if n < 0 or first + n > self.n:
            raise ValueError('Invalid parameters value: first_trace=%d, n=%d (number of traces=%d)' % (first_trace, n, self.n))

        self.t = self.t[first:first+n]
        self.p = self.p[first:first+n]
        self.c = self.c[first:first+n]
        self.n = n

    def shrink (self, chunk_size):
        """Shrink all the traces of the context, by replacing each chunk
        of `chunk_size` points by their sum. If incomplete, the last chunk is discarded

        Args:
            chunk_size (int): Number of points per chunk.

        """

        if not isinstance (chunk_size, int):
            raise TypeError('parameter chunk_size should be a number')
        if chunk_size < 1 or chunk_size > self.l:
            raise ValueError('Invalid parameters value: chunk_size=%d (traces length=%d)' % (chunk_size, self.l))

        self.l = self.l / chunk_size
        self.t = [[sum(tt[i*chunk_size:(i+1)*chunk_size]) for i in range(self.l)] for tt in self.t]

    def dump (self, filename):
        """Writes the context in a HWSec trace file `filename`

        Args:
            filename (str): Name of output HWSec trace file.

        """
        
        with open(str(filename), 'wb') as f:
            f.write (struct.pack ("<" + str(len(HWSECMAGICNUMBER)) + "siiQ", HWSECMAGICNUMBER, self.n, self.l, self.k))

            for p, c, t in zip (self.p, self.c, self.t):
                f.write (struct.pack ("<QQ" + str(self.l) + "f", tuple([p, c] + t)))


def plot (prefix, i, t):
    """Create two gnuplot files for a set of traces. `prefix`.dat is the data file
    containing the `n` traces `t[0]` ... `t[n-1]` in gnuplot format. `prefix`.cmd
    is a gnuplot command file that can be used to plot them with the command::

    $ gnuplot -persist prefix.cmd

    If the parameter `i` is the index of one of the traces (0 <= `i` <= `n`-1), the
    corresponding trace will be plotted in red and with the title "Trace X (0xY)" where
    X and Y are the decimal and hexadecimal forms of `i`. All the other traces are
    plotted in blue without title.

    Args:
        prefix (str): The prefix of the two file names. The data file name is prefix.dat
                      and the gnuplot command file name is prefix.cmd
        i (int): The index of a trace to plot in red. None if not in the 0..n-1 range.
        t (List[List[float]]): The traces.

    """

    if not isinstance (i, int):
        raise TypeError('parameter i should be a number')

    n = len(t)

    title = None
    if i >= 0 and i < n:
        title = "Trace #%d (0x%x)" % (i, i)
    else:
        i = -1

    with open ("%s.cmd" % str(prefix), 'w') as fpc:
        fname = "%s.dat" % str(prefix)
        with open (fname, 'w') as fpd:
            fpc.write ("plot \\\n")
            for ii, tt in enumerate (t):
                for p in tt:
                    fpd.write ("%e\n" % p)
                fpd.write ("\n\n")
                if ii != i:
                    fpc.write ("'%s' index %d notitle with lines linecolor 3" % (fname, ii))
                    if i != -1 or ii != n-1:
                        fpc.write (",\\\n")
            if i != -1:
                fpc.write ("'%s' index %d title '%s' with lines linecolor 1" % (fname, i, title))
            fpc.write ("\n")
