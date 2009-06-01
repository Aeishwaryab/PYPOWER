# Copyright (C) 2009 Richard W. Lincoln
#
# This program is free software, you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 2 dated June, 1991.
#
# This software is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY, without even the implied warranty of
# MERCHANDABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program, if not, write to the Free Software Foundation,
# Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA

""" PYPOWER options dictionary.

Ported from:
    D. Zimmerman, "mpoption.m", MATPOWER, version 3.2,
    Power System Engineering Research Center (PSERC), 2007

See http://www.pserc.cornell.edu/matpower/ for more info.

The currently defined options are as follows:

 idx - NAME, default          description [options]
 ---   -------------          -------------------------------------
power flow options
  1  - PF_ALG, 1              power flow algorithm
      [   1 - Newton's method                                     ]
      [   2 - Fast-Decoupled (XB version)                         ]
      [   3 - Fast-Decoupled (BX version)                         ]
      [   4 - Gauss Seidel                                        ]
  2  - PF_TOL, 1e-8           termination tolerance on per unit
                              P & Q mismatch
  3  - PF_MAX_IT, 10          maximum number of iterations for
                              Newton's method
  4  - PF_MAX_IT_FD, 30       maximum number of iterations for
                              fast decoupled method
  5  - PF_MAX_IT_GS, 1000     maximum number of iterations for
                              Gauss-Seidel method
  6  - ENFORCE_Q_LIMS, 0      enforce gen reactive power limits,
                              at expense of |V|       [   0 or 1  ]
  10 - PF_DC, 0               use DC power flow formulation, for
                              power flow and OPF
      [    0 - use AC formulation & corresponding algorithm opts  ]
      [    1 - use DC formulation, ignore AC algorithm options    ]
OPF options
  11 - OPF_ALG, 0             algorithm to use for OPF
      [    0 - choose best default solver available in the        ]
      [        following order, 500, 540, 520 then 100/200        ]
      [ Otherwise the first digit specifies the problem           ]
      [ formulation and the second specifies the solver,          ]
      [ as follows, (see the User's Manual for more details)      ]
      [  100 - standard formulation (old), constr                 ]
      [  120 - standard formulation (old), dense LP               ]
      [  140 - standard formulation (old), sparse LP (relaxed)    ]
      [  160 - standard formulation (old), sparse LP (full)       ]
      [  200 - CCV formulation (old), constr                      ]
      [  220 - CCV formulation (old), dense LP                    ]
      [  240 - CCV formulation (old), sparse LP (relaxed)         ]
      [  260 - CCV formulation (old), sparse LP (full)            ]
      [  500 - generalized formulation, MINOS                     ]
      [  520 - generalized formulation, fmincon                   ]
      [  540 - generalized formulation, PDIPM                     ]
      [        primal/dual interior point method                  ]
      [  545 - generalized formulation (except CCV), SCPDIPM      ]
      [        step-controlled primal/dual interior point method  ]
      [  550 - generalized formulation, TRALM                     ]
      [        trust region based augmented Langrangian method    ]
      [ See the User's Manual for details on the formulations.    ]
  12 - OPF_ALG_POLY, 100      default OPF algorithm for use with
                              polynomial cost functions
                              (used only if no solver available
                              for generalized formulation)
  13 - OPF_ALG_PWL, 200       default OPF algorithm for use with
                              piece-wise linear cost functions
                              (used only if no solver available
                              for generalized formulation)
  14 - OPF_POLY2PWL_PTS, 10   number of evaluation points to use
                              when converting from polynomial to
                              piece-wise linear costs
  16 - OPF_VIOLATION, 5e-6    constraint violation tolerance
  17 - CONSTR_TOL_X, 1e-4     termination tol on x for copf & fmincopf
  18 - CONSTR_TOL_F, 1e-4     termination tol on F for copf & fmincopf
  19 - CONSTR_MAX_IT, 0       max number of iterations for copf & fmincopf
                              [       0 => 2*nb + 150             ]
  20 - LPC_TOL_GRAD, 3e-3     termination tolerance on gradient for lpopf
  21 - LPC_TOL_X, 1e-4        termination tolerance on x (min step size)
                              for lpopf
  22 - LPC_MAX_IT, 400        maximum number of iterations for lpopf
  23 - LPC_MAX_RESTART, 5     maximum number of restarts for lpopf
  24 - OPF_FLOW_LIM, 0        qty to limit for branch flow constraints
      [   0 - apparent power flow (limit in MVA)                  ]
      [   1 - active power flow (limit in MW)                     ]
      [   2 - current magnitude (limit in MVA at 1 p.u. voltage   ]
  25 - OPF_IGNORE_ANG_LIM, 0  ignore angle difference limits for branches
                              even if specified       [   0 or 1  ]
output options
  31 - VERBOSE, 1             amount of progress info printed
      [   0 - print no progress info                              ]
      [   1 - print a little progress info                        ]
      [   2 - print a lot of progress info                        ]
      [   3 - print all progress info                             ]
  32 - OUT_ALL, -1            controls printing of results
      [  -1 - individual flags control what prints                ]
      [   0 - don't print anything                                ]
      [       (overrides individual flags, except OUT_RAW)        ]
      [   1 - print everything                                    ]
      [       (overrides individual flags, except OUT_RAW)        ]
  33 - OUT_SYS_SUM, 1         print system summary    [   0 or 1  ]
  34 - OUT_AREA_SUM, 0        print area summaries    [   0 or 1  ]
  35 - OUT_BUS, 1             print bus detail        [   0 or 1  ]
  36 - OUT_BRANCH, 1          print branch detail     [   0 or 1  ]
  37 - OUT_GEN, 0             print generator detail  [   0 or 1  ]
                              (OUT_BUS also includes gen info)
  38 - OUT_ALL_LIM, -1        control constraint info output
      [  -1 - individual flags control what constraint info prints]
      [   0 - no constraint info (overrides individual flags)     ]
      [   1 - binding constraint info (overrides individual flags)]
      [   2 - all constraint info (overrides individual flags)    ]
  39 - OUT_V_LIM, 1           control output of voltage limit info
      [   0 - don't print                                         ]
      [   1 - print binding constraints only                      ]
      [   2 - print all constraints                               ]
      [   (same options for OUT_LINE_LIM, OUT_PG_LIM, OUT_QG_LIM) ]
  40 - OUT_LINE_LIM, 1        control output of line limit info
  41 - OUT_PG_LIM, 1          control output of gen P limit info
  42 - OUT_QG_LIM, 1          control output of gen Q limit info
  43 - OUT_RAW, 0             print raw data for Perl database
                              interface code          [   0 or 1  ]
"""

options = {
    # power flow options
    'PF_ALG':         2,      # 1  - PF_ALG
    'PF_TOL':         1e-8,   # 2  - PF_TOL
    'PF_MAX_IT':      10,     # 3  - PF_MAX_IT
    'PF_MAX_IT_FD':   30,     # 4  - PF_MAX_IT_FD
    'PF_MAX_IT_GS':   1000,   # 5  - PF_MAX_IT_GS
    'ENFORCE_Q_LIMS': 0,      # 6  - ENFORCE_Q_LIMS
    'RESERVED7':      0,      # 7  - RESERVED7
    'RESERVED8':      0,      # 8  - RESERVED8
    'RESERVED9':      0,      # 9  - RESERVED9
    'PF_DC':          0,      # 10 - PF_DC

    # OPF options
    'OPF_ALG_POLY':  0,      # 11 - OPF_ALG_POLY
    'OPF_ALG_POLY':  100,    # 12 - OPF_ALG_POLY
    'OPF_ALG_PWL':   200,    # 13 - OPF_ALG_PWL
    'OPF_POLY2PWL_PTS': 10,  # 14 - OPF_POLY2PWL_PTS
    'OPF_NEQ':       0,      # 15 - OPF_NEQ
    'OPF_VIOLATION': 5e-6,   # 16 - OPF_VIOLATION
    'CONSTR_TOL_X':  1e-4,   # 17 - CONSTR_TOL_X
    'CONSTR_TOL_F':  1e-4,   # 18 - CONSTR_TOL_F
    'CONSTR_MAX_IT': 0,      # 19 - CONSTR_MAX_IT
    'LPC_TOL_GRAD':  3e-3,   # 20 - LPC_TOL_GRAD
    'LPC_TOL_X':     1e-4,   # 21 - LPC_TOL_X
    'LPC_MAX_IT':    400,    # 22 - LPC_MAX_IT
    'LPC_MAX_RESTART': 5,    # 23 - LPC_MAX_RESTART
    'OPF_FLOW_LIM':  0,      # 24 - OPF_FLOW_LIM
    'OPF_IGNORE_ANG_LIM': 0, # 25 - OPF_IGNORE_ANG_LIM
    'RESERVED26': 0,         # 26 - RESERVED26
    'RESERVED27': 0,         # 27 - RESERVED27
    'RESERVED28': 0,         # 28 - RESERVED28
    'RESERVED29': 0,         # 29 - RESERVED29
    'RESERVED30': 0,         # 30 - RESERVED30

    # output options
    'VERBOSE':      1,      # 31 - VERBOSE
    'OUT_ALL':      0,     # 32 - OUT_ALL
    'OUT_SYS_SUM':  1,      # 33 - OUT_SYS_SUM
    'OUT_AREA_SUM': 0,      # 34 - OUT_AREA_SUM
    'OUT_BUS':      1,      # 35 - OUT_BUS
    'OUT_BRANCH':   1,      # 36 - OUT_BRANCH
    'OUT_GEN':      0,      # 37 - OUT_GEN
    'OUT_ALL_LIM': -1,     # 38 - OUT_ALL_LIM
    'OUT_V_LIM':    1,      # 39 - OUT_V_LIM
    'OUT_LINE_LIM': 1,      # 40 - OUT_LINE_LIM
    'OUT_PG_LIM':   1,      # 41 - OUT_PG_LIM
    'OUT_QG_LIM':   1,      # 42 - OUT_QG_LIM
    'OUT_RAW':      0,      # 43 - OUT_RAW
    'RESERVED44':   0,      # 44 - RESERVED44
    'RESERVED45':   0,      # 45 - RESERVED45
    'RESERVED46':   0,      # 46 - RESERVED46
    'RESERVED47':   0,      # 47 - RESERVED47
    'RESERVED48':   0,      # 48 - RESERVED48
    'RESERVED49':   0,      # 49 - RESERVED49
    'RESERVED50':   0,      # 50 - RESERVED50
}
