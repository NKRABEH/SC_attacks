#! /usr/bin/env python2

#
# Copyright (C) Telecom ParisTech
# 
# This file must be used under the terms of the CeCILL. This source
# file is licensed as described in the file COPYING, which you should
# have received as part of this distribution. The terms are also
# available at:
# http://www.cecill.info/licences/Licence_CeCILL_V1.1-US.txt
#

# THIS IS NOT A REAL POWER ATTACK: it assumes that the last round key is
# 0x0123456789ab. Your goal is to retrieve the true last round key, instead.

import sys
import argparse

import des
import traces
import tr_pcc
import numpy as np

# The P permutation table, as in the standard. The first entry (16) is the
# position of the first (leftmost) bit of the result in the input 32 bits word.
# Used to convert target bit index into SBox index (just for printed summary
# after attack completion).
p_table = [16, 7, 20, 21, 29, 12, 28, 17, 1, 15, 23, 26, 5, 18, 31, 10, 2, 8, 24, 14, 32, 27, 3, 9, 19, 13, 30, 6, 22, 11, 4, 25]



def main ():
    # ************************************************************************
    # * Before doing anything else, check the correctness of the DES library *
    # ************************************************************************
    if not des.check ():
        sys.exit ("DES functional test failed")


    # *************************************
    # * Check arguments and read datafile *
    # *************************************
    argparser = argparse.ArgumentParser(description="Apply P. Kocher's DPA algorithm based on decision function")
    argparser.add_argument("datafile", metavar='FILE', 
                        help='name of the traces file in HWSec format. (e.g.  pa.hws)')
    argparser.add_argument("n", metavar='N', type=int,
                        help='number of acquisitions to use')
    argparser.add_argument("target_bit", metavar='[B]', type=int, nargs='?', default=1,
                        help='index of target bit in L15 (1 to 32, as in DES standard, default: 1)')
    args = argparser.parse_args()

    if args.n < 1:                                      # If invalid number of acquisitions.
        sys.exit ("Invalid number of acquisitions: %d (shall be greater than 1)" % args.n)

    if args.target_bit < 1 or args.target_bit > 32:     # If invalid target bit index.
        sys.exit ("Invalid target bit index: %d (shall be between 1 and 32 included)" % args.target_bit)

    # Compute index of corresponding SBox
    #target_sbox = (p_table[args.target_bit - 1] - 1) / 4 + 1
    # Read power traces and ciphertexts. n is the number of acquisitions to use.
    ctx = read_datafile (args.datafile, args.n)


    # *****************************************************************************
    # * Compute and print average power trace. Store average trace in file        *
    # * "average.dat" and gnuplot command in file "average.cmd". In order to plot *
    # * the average power trace, type: $ gnuplot -persist average.cmd             *
    # *****************************************************************************
    #average (ctx, "average")


    # ***************************************************************
    # * Attack target bit in L15=R14 with P. Kocher's DPA technique *
    # ***************************************************************

    tr= [[t[i] for t in ctx.t] for i in range(575,600)] 
    key=0x000000000000
    for sbox in range(8):
        pccs=[]
        for i in range(64):
            d=[]
            for ct, t in zip (ctx.c, ctx.t):
                r16l16 = des.ip (ct)            # Compute R16|L16
                l16 = des.right_half (r16l16)   # Extract right half
                r16 = des.left_half (r16l16)    # Extract left half
                er15 = des.e (l16)              # Compute E(R15) = E(L16)
                rk = i * 0x041041041041
                l15 = r16 ^ des.p (des.sboxes (er15 ^ rk))          # Compute L15 
                hd = hamming_distance(l16, l15, sbox)
                d.append(hd)
            c = tr_pcc.pcc(d, tr)
            pccs.append(np.max(np.abs(np.array(c))))
        best = np.argmax(pccs)
        #bk= '{0:04b}'.format(best)
        key |= (best<< (42 - 6*sbox))
        

    
    #dpa, best_guess, best_max, best_idx = dpa_attack (ctx, args.target_bit)


    # *******************************************************************************
    # * Print the 64 DPA traces in a data file named dpa.dat. Print corresponding   *
    # * gnuplot commands in a command file named dpa.cmd. All DPA traces are        *
    # * plotted in blue but the one corresponding to the best guess which is        *
    # * plotted in red with the title "Trace X (0xY)" where X and Y are the decimal *
    # * and heaxdecimal forms of the 6 bits best guess.                             *
    # *******************************************************************************
    # Plot DPA traces in dpa.dat, gnuplot commands in dpa.cmd
    #traces.plot ("dpa", best_guess, dpa)


    # *****************
    # * Print summary *
    # *****************
    '''print >> sys.stderr, "Target bit: %d" % args.target_bit
    print >> sys.stderr, "Target SBox: %d" % target_sbox
    print >> sys.stderr, "Best guess: %d (0x%02x)" % (best_guess, best_guess)
    print >> sys.stderr, "Maximum of DPA trace: %e" % best_max
    print >> sys.stderr, "Index of maximum in DPA trace: %d" % best_idx
    print >> sys.stderr, "DPA traces stored in file 'dpa.dat'. In order to plot them, type:"
    print >> sys.stderr, "$ gnuplot -persist dpa.cmd"

    # ************************
    # * Print last round key *
    # ************************
    rk = 0x0123456789ab
    print >> sys.stderr, "Last round key (hex):"'''
    print ("0x%012X" % key)


# A function to allocate cipher texts and power traces, read the
# datafile and store its content in allocated context.
def read_datafile (name, n):
    ctx = traces.trContext (name, n)
    if ctx.n != n:
        sys.exit ("Could not read %d acquisitions from traces file. Traces file contains %d acquisitions." % (n, ctx.n));

    return ctx



# Compute the average power trace of the traces context ctx, print it in file
# <prefix>.dat and print the corresponding gnuplot command in <prefix>.cmd. In
# order to plot the average power trace, type: $ gnuplot -persist <prefix>.cmd
def average (ctx, prefix):
    acc = [sum(i) for i in zip(*ctx.t)]
    avg = [i/len(ctx.t) for i in acc]

    traces.plot (prefix, -1, [avg]);
    print >> sys.stderr, "Average power trace stored in file '%s.dat'. In order to plot it, type:" % prefix
    print >> sys.stderr, "$ gnuplot -persist %s.cmd" % prefix



# Decision function: takes a ciphertext and returns an array of 64 values for
# an intermediate DES data, one per guess on a 6-bits subkey. In this example
# the decision is the computed value of bit index <target_bit> of L15. Each of
# the 64 decisions is thus 0 or 1.
def decision (ct, target_bit):
    r16l16 = des.ip (ct)            # Compute R16|L16
    l16 = des.right_half (r16l16)   # Extract right half
    r16 = des.left_half (r16l16)    # Extract left half
    er15 = des.e (l16)              # Compute E(R15) = E(L16)

    d = []
    # For all guesses (64). rk is a 48 bits last round key with all 6-bits
    # subkeys equal to current guess g (nice trick, isn't it?).
    for g in xrange (64):
        rk = g * 0x041041041041
        l15 = r16 ^ des.p (des.sboxes (er15 ^ rk))          # Compute L15
        d.append ((l15 >> (32 - target_bit)) & 1)           # Extract value of target bit

    return d



# Apply P. Kocher's DPA algorithm based on decision function. Computes 64 DPA
# traces dpa[0..63], best_guess (6-bits subkey corresponding to highest DPA
# peak), best_idx (index of sample with maximum value in best DPA trace) and
# best_max (value of sample with maximum value in best DPA trace).
def dpa_attack (ctx, target_bit):
    t0 = [[0.0] * ctx.l] * 64
    n0 = [0] * 64
    t1 = [[0.0] * ctx.l] * 64
    n1 = [0] * 64
    for ct, t in zip (ctx.c, ctx.t):                        # For all acquisitions
        d = decision (ct, target_bit)                       # Compute the 64 decisions

        # For all guesses (64)
        for g in xrange (64):
            if d[g] == 0:                                   # If decision on target bit is zero
                t0[g] = [a+b for a,b in zip (t0[g], t)]     # Accumulate power trace in zero-set
                n0[g] += 1                                  # Increment traces count for zero-set
            else:                                           # If decision on target bit is one
                t1[g] = [a+b for a,b in zip (t1[g], t)]     # Accumulate power trace in one-set
                n1[g] += 1                                  # Increment traces count for one-set

    # Compute normalized one-set minus zero-set
    dpa = [[t1[g][i]/n1[g] - t0[g][i]/n0[g] for i in xrange (ctx.l)] for g in xrange (64)]

    # Get max and argmax for each guess
    maxs = [max(l) for l in dpa]
    idx = [l.index(m) for l,m in zip (dpa, maxs)]

    # Get best maximum
    best_max = max (maxs)
    best_guess = maxs.index (best_max)
    best_idx = idx[best_guess]

    return dpa, best_guess, best_max, best_idx


def hamming_distance(x, y, i):
    #x_bin='{:032b}'.format(x)
    #y_bin='{:032b}'.format(y)
    np_x=des.n_p(x)
    np_y=des.n_p(y)
    np_x_bin='{:032b}'.format(np_x)
    np_y_bin='{:032b}'.format(np_y)
    d=0
    for j in range(4):
        if np_x_bin[4*i+j]!=np_y_bin[4*i+j]:
            d+=1
    return(d)

if __name__ == "__main__":
    main ()
