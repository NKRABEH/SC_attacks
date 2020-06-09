#!/usr/bin/env python2

# MASTER-ONLY: DO NOT MODIFY THIS FILE

#
# Copyright (C) Telecom ParisTech
# 
# This file must be used under the terms of the CeCILL. This source
# file is licensed as described in the file COPYING, which you should
# have received as part of this distribution. The terms are also
# available at:
# http://www.cecill.info/licences/Licence_CeCILL_V1.1-US.txt
#

"""
Provides pcc function to estimate Pearson Correlation Coefficients (PCC)

Date:    2019-04-25
Authors: Renaud Pacalet, renaud.pacalet@telecom-paristech.fr

The Pearson Correlation Coefficient (PCC) is a statistical tool to evaluate the
linear correlation between two random variables. The formula of a PCC between
random variables X and Y is:

PCC(X,Y) = [E(X*Y) - E(X)*E(Y)] / [s(X) * s(Y)]

where E(Z) is the expectation (average value) of random variable Z and s(Z) is
its standard deviation. The value of the PCC is in range -1 to +1. Values close
to 0 indicate no or a weak linear correlation. Values close to -1 or +1
indicate strong linear correlations.

The basic form of the pcc function computes an estimate of PCC(X,Y), the
Pearson Correlation Coefficient between two scalar random variables X and Y. It
computes the estimate from two samples of X and Y. The samples must contain the
same number N of observations, with N>=2. The samples are passed as two lists
of N numbers:

x = [0]*N
y = [0]*N
p = 0
...
p = tr_pcc.pcc(x,y)

The returned value is a floating point number between -1.0 and 1.0.

In a second form the pcc function computes the K estimates of PCC(X,Yk),
0<=k<K. The Yk are K distinct scalar random variables. Their samples are passed
as a list of K lists of N>=2 numbers each, where N is the length of the
sublists and also of the list representing the sample of  X. This second form
returns the list of the K PCC estimates:

x = [0]*N
y = [[0]*N for k in range(K)]
p = [0]*K
...
p = tr_pcc.pcc(x,y)

A third and fourth forms are the equivalents of the two first forms but where X
is a L-components vector random variable. The PCC estimates are computed
component-wise of X:

x = [[0]*L for n in range(N)]
y = [0]*N
z = [[0]*N for k in range(K)]
pxy = [0]*L
pxz = [[0]*L for k in range(K)]
...
pxy = tr_pcc.pcc(x,y)
pxz = tr_pcc.pcc(x,z)

Usage:
    import tr_pcc

    x0 = [0]*N
    x1 = [[0]*L for n in range(N)]
    y0 = [0]*N
    y1 = [[0]*N for k in range(K)]
    px0y0 = 0
	px0y1 = [0]*K
    px1y0 = [0]*L
	px1y1 = [[0]*L for k in range(K)]
    ...
    px0y0 = tr_pcc.pcc(x0,y0)
    px0y1 = tr_pcc.pcc(x0,y1)
    px1y0 = tr_pcc.pcc(x1,y0)
    px1y1 = tr_pcc.pcc(x1,y1)

"""

import numbers
import numpy as np

# import math

def pcc(x, y):
	"""
Computes an estimate of the PCC between random variables X and Y

First form:
    Args:
        x (list of N floats, N>1): N-points sample of random variable X
        y (list of N floats, N>1): N-points sample of random variable Y
    
    Returns:
        float: PCC estimate of random variables X and Y

    Example:
        import tr_pcc
        ...
        x = [0]*N                       # X sample
        y = [0]*N                       # Y sample
        p = 0                           # PCC estimate
        for n in range (N):             # For N draws
            x[n] = draw_X               # Draw random variable X
            y[n] = draw_Y               # Draw random variable Y
        p = tr_pcc.pcc (x,y)               # Compute PCC(X,Y) estimate
        print ("PCC(X,Y) = %lf" % p)    # Print PCC estimate
        ...

Second form:
    Args:
        x (list of N floats, N>1): N-points sample of random variable X
        y (list of K lists of N floats, N>1): K different N-points
            samples of random variables Y0,Y1,...,YK-1
    
    Returns:
        list of K floats: PCC estimates of random variables X and Y0,
            X and Y1,..., X and YK-1

    Example:
        import tr_pcc
        ...
        x = [0]*N                         # X sample
        y = [[0]*N for k in range(K)]     # Yk samples, 0<=k<K
        p = [0]*K                         # K PCC estimates
        for n in range (N):               # For N draws
            x[n] = draw_X                 # Draw random variable X
            for k in range (K):           # For K random variables Yk
                y[k][n] = draw_Y (k)      # Draw random variable Yk
        p = tr_pcc.pcc (x,y)                 # Compute PCC(X,Yk) estimates, 0<=k<K
        for k in range (K):               # For K PCC estimates
            print ("PCC(X,Y%d)=%lf" % (k,p[k])) # Print PCC estimates
        ...

Third form:
    Args:
        x (list of N lists of L floats, N>1): N-points sample of vector random variable X
        y (list of N floats, N>1): N-points sample of random variable Y
    
    Returns:
        list of L floats: PCC estimate of random variables X and Y

    Example:
        import tr_pcc
        ...
        x = [[0]*L for n in range(N)]   # X sample
        y = [0]*N                       # Y sample
        p = [0]*L                       # PCC estimate
        for n in range (N):             # For N draws
            for l in range (L):         # For L components
                x[n][l] = draw_X (l)    # Draw component of random variable X
            y[n] = draw_Y               # Draw random variable Y
        p = tr_pcc.pcc (x,y)               # Compute PCC(X,Y) estimate
        for l in range (L):             # For L components
			print ("PCC(X,Y)[%d] = %lf" % (l,p[l])) # Print component of PCC estimate
        ...

Fourth form:
    Args:
        x (list of N lists of L floats, N>1): N-points sample of vector random variable X
        y (list of K lists of N floats, N>1): K different N-points
            samples of random variables Y0,Y1,...,YK-1
    
    Returns:
        list of K lists of L floats: PCC estimates of random variables X and Y0,
            X and Y1,..., X and YK-1

    Example:
        import tr_pcc
        ...
        x = [[0]*L for n in range(N)]   # X sample
        y = [[0]*N for k in range(K)]   # Yk samples, 0<=k<K
        p = [[0]*L for k in range(K)]   # PCC estimate
        for n in range (N):             # For N draws
            for l in range (L):         # For L components
                x[n][l] = draw_X (l)    # Draw component of random variable X
            for k in range (K):         # For K random variables Yk
                y[k][n] = draw_Y (k)    # Draw random variable Yk
        p = tr_pcc.pcc (x,y)               # Compute PCC(X,Y) estimate
        for k in range (K):             # For K PCC estimates
            for l in range (L):         # For L components
			    print ("PCC(X,Y%d)[%d] = %lf" % (k,l,p[k][l])) # Print component of PCC estimate
        ...

Raises:
    TypeError: x,y lengths mismatch (first form)
    TypeError: x,y-sub-lists lengths mismatch (second form)
    TypeError: x not list of floats and not list of lists of floats
    TypeError: y not list of floats and not list of lists of floats
    ValueError: length of x < 2
    ValueError: x variance estimate=0 (constant x?)
    ValueError: y variance estimate=0 (constant y?)

Note:
    The second and fourth forms are equivalent to:
        p = map(lambda z:tr_pcc.pcc(x,z),y)
    but are much more efficient.
"""

	# check types
	if not isinstance(x, list):
		raise TypeError('X must be a list of numbers or a list of lists of numbers')
	if not isinstance(y, list):
		raise TypeError('Y must be a list of numbers or a list of lists of numbers')

	x0 = len(x)
	y0 = len(y)
	if (x0 < 2):
		raise ValueError('samples with less than 2 values are not supported')

	if all(isinstance(item, numbers.Number) for item in x):
		x1 = 0
	elif all(isinstance(item, list) for item in x):
		x1 = len(x[0])
		if not all(len(item) == x1 for item in x):
			raise TypeError('X realizations of different lengths are not supported')
		if not all(all(isinstance(item, numbers.Number) for item in row) for row in x):
			raise TypeError('X must be a list of numbers or a list of lists of numbers')

	if all(isinstance(item, numbers.Number) for item in y):
		y1 = 0
	elif all(isinstance(item, list) for item in y):
		y1 = len(y[0])
		if not all(len(item) == y1 for item in y):
			raise TypeError('Y realizations of different lengths are not supported')
		if not all(all(isinstance(item, numbers.Number) for item in row) for row in y):
			raise TypeError('Y must be a list of numbers or a list of lists of numbers')

	if (y1 == 0 and x0 != y0) or (y1 != 0 and x0 != y1):
			raise TypeError('samples of different lengths are not supported')

	xarray = np.asarray(x, dtype=np.float64)
	yarray = np.asarray(y, dtype=np.float64)
	if x1 == 0:
		sum_x = np.sum(xarray)
		sum_x2 = np.sum(xarray * xarray)
		std_x = np.sqrt(x0 * sum_x2 - sum_x * sum_x)
		if std_x == 0.0:
			raise ValueError('variance(X)=0')
	else:
		sum_x = np.sum(xarray, axis=0)
		sum_x2 = np.apply_along_axis(lambda t:sum(t * t), 0, xarray)
		std_x = np.sqrt(x0 * sum_x2 - sum_x * sum_x)
		if any(item == 0.0 for item in std_x):
			raise ValueError('variance(X)=0 at indexes ' + numpy.where(std_x == 0.0)[0])
	if y1 == 0:
		sum_y = np.sum(yarray)
		sum_y2 = np.sum(yarray * yarray)
		std_y = np.sqrt(y0 * sum_y2 - sum_y * sum_y)
		if std_y == 0.0:
			raise ValueError('variance(Y)=0')
	else:
		sum_y = np.sum(yarray, axis=1)
		sum_y2 = np.apply_along_axis(lambda t:sum(t * t), 1, yarray)
		std_y = np.sqrt(y1 * sum_y2 - sum_y * sum_y)
		if any(item == 0.0 for item in std_y):
			raise ValueError('variance(Y)=0 at indexes ' + numpy.where(std_y == 0.0)[0])

	sum_xy = np.dot(xarray.T, yarray.T)
	p = (x0 * sum_xy - np.outer(sum_x.T, sum_y)) / np.outer(std_x, std_y)
	return p.T.tolist()

# vim: set tabstop=4 softtabstop=4 shiftwidth=4 noexpandtab textwidth=0:
