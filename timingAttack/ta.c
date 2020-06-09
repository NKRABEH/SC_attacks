/*
 * Copyright (C) Telecom ParisTech
 * 
 * This file must be used under the terms of the CeCILL. This source
 * file is licensed as described in the file COPYING, which you should
 * have received as part of this distribution. The terms are also
 * available at:
 * http://www.cecill.info/licences/Licence_CeCILL_V1.1-US.txt
*/

/* THIS IS NOT A REAL TIMING ATTACK: it assumes that the last round key is
 * 0x0123456789ab. Your goal is to retrieve the true last round key, instead. */

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <inttypes.h>
#include "pcc.h"
#include "utils.h"
#include "des.h"
#include "km.h"

uint64_t *ct; /* Array of cipher texts. */
double *t; /* Array of timing measurements. */

/* Allocate arrays <ct> and <t> to store <n> cipher texts and timing
 * measurements. Open datafile <name> and store its content in global variables
 * <ct> and <t>. */
void
read_datafile(char *name, int n);

int
main(int argc, char **argv) {
  int n; /* Required number of experiments. */
  uint64_t r16l16; /* Output of last round, before final permutation. */
  uint64_t l16; /* Right half of r16l16. */
  uint64_t sbo; /* Output of SBoxes during last round. */
  double sum; /* Sum of timing measurements. */
  int i; /* Loop index. */
  uint64_t rk; /* Round key */

  /************************************************************************/
  /* Before doing anything else, check the correctness of the DES library */
  /************************************************************************/
  if(!des_check()) {
    ERROR(0, -1, "DES functional test failed");
  }

  /*************************************/
  /* Check arguments and read datafile */
  /*************************************/
  /* If invalid number of arguments (including program name), exit with error
   * message. */
  if(argc != 3) {
    ERROR(0, -1, "usage: ta <datafile> <nexp>\n");
  }
  /* Number of experiments to use is argument #2, convert it to integer and
   * store the result in variable n. */
  n = atoi(argv[2]);
  if(n < 1) { /* If invalid number of experiments. */
    ERROR(0, -1, "number of experiments to use (<nexp>) shall be greater than 1 (%d)", n);
  }
  /* Read data. Name of data file is argument #1. Number of experiments to use is n. */
  read_datafile(argv[1], n);

  /*****************************************************************************
   * Compute the Hamming weight of output of first (leftmost) SBox during last *
   * round, under the assumption that the last round key is 0x0123456789ab     *
   *****************************************************************************/
rk= UINT64_C(0x000000000000); // Assume the key is 0
uint64_t best=UINT64_C(0x0); // most probable key for sbox input
uint64_t key;
int hw=0;
double c0,c;
pcc_context *ctx;
for (int s=0;s<8;s++)// sbox from 1 to 8 
{	// printf("\n %d",s);
	
	c0=0; // best correlation coeff
	for (uint64_t i=0; i<64 ; i++) 
	{	ctx=pcc_init(1);
		key =  i << (42 - 6*s);
		
		for (int j=0; j< n; j++ )
			{
			r16l16=des_ip(ct[j]);
			l16 = des_right_half(r16l16);
			//printf("0x%016"PRIx64, rk  ) ; 
			//printf("\n");UINT64_C(0x0000003f)
			sbo = des_sbox(s+1 , ((des_e(l16) >> 6*(7-s)) & UINT64_C(0x0000003f)) ^  i  );
			// Compute Hamming weight of output SBox
			hw=hamming_weight(sbo );
			pcc_insert_x(ctx,t[j]);
	    		pcc_insert_y(ctx,0,hw);	
			}
		//printf("\n %d",i); 
		pcc_consolidate(ctx);
		c= pcc_get_pcc(ctx,0);
		if (c>c0)
		{
		c0=c;
		best = key; 
		}
	}
	
	rk |= best;
	//printf("0x%016"PRIx64, rk  ) ;
	pcc_free(ctx);
}

  /************************************
   * Compute and print average timing *
   ************************************/
  sum = 0.0; /* Initializes the accumulator for the sum of timing measurements. */
  for(i = 0; i < n; i++) { /* For all n experiments. */
    sum = sum + t[i]; /* Accumulate timing measurements. */
  }
  /* Compute and print average timing measurements. */
  fprintf(stderr, "Average timing: %f\n", sum / (double)(n));

  /************************
   * Print last round key *
   ************************/
  fprintf(stderr, "Last round key (hex):\n");
  printf("0x%012" PRIx64 "\n", rk);

  free(ct); /* Deallocate cipher texts */
  free(t); /* Deallocate timings */
  return 0; /* Exits with "everything went fine" status. */
}

void
read_datafile(char *name, int n) {
  FILE *fp; /* File descriptor for the data file. */
  int i; /* Loop index */

  /* Open data file for reading, store file descriptor in variable fp. */
  fp = XFOPEN(name, "r");

  /* Allocates memory to store the cipher texts and timing measurements. Exit
   * with error message if memory allocation fails. */
  ct = XCALLOC(n, sizeof(uint64_t));
  t = XCALLOC(n, sizeof(double));

  /* Read the n experiments (cipher text and timing measurement). Store them in
   * the ct and t arrays. Exit with error message if read fails. */
  for(i = 0; i < n; i++) {
    if(fscanf(fp, "%" PRIx64 " %lf", &(ct[i]), &(t[i])) != 2) {
      ERROR(, -1, "cannot read cipher text and/or timing measurement");
    }
  }
}
