# Copyright (C) 1996-2010 Power System Engineering Research Center
# Copyright (C) 2010 Richard Lincoln <r.w.lincoln@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from numpy import array

def case6bus():
    """6-bus system
    From in problem 3.6 in book 'Computational
    Methods for Electric Power Systems' by Mariesa Crow

    @author: Rui Bo
    @author: Richard Lincoln
    @see: U{http://www.pserc.cornell.edu/matpower/}
    """
    ppc = {}
    ##-----  Power Flow Data  -----##
    ## system MVA base
    ppc["baseMVA"] = 100.0

    ## bus data
    # bus_i, type, Pd, Qd, Gs, Bs, area, Vm, Va, baseKV, zone, Vmax, Vmin
    ppc["bus"] = array([
        [1, 3, 0.25, 0.1, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9],
        [2, 2, 0.15, 0.05, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9],
        [3, 1, 0.275, 0.11, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9],
        [4, 1, 0, 0, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9],
        [5, 1, 0.15, 0.09, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9],
        [6, 1, 0.25, 0.15, 0, 0, 1, 1, 0, 230, 1, 1.1, 0.9]
    ])

    ppc["bus"][:, 2] = ppc["bus"][:, 2] * ppc["baseMVA"]
    ppc["bus"][:, 3] = ppc["bus"][:, 3] * ppc["baseMVA"]

    ## generator data
    # Note:
    # 1)It's better of gen to be in number order, otherwise gen and genbid
    # should be sorted to make the lp solution output clearly(in number order as well)
    # 2)set Pmax to nonzero. set to 999 if no limit
    # 3)If change the order of gen, then must change the order in genbid
    # accordingly
    # bus, Pg, Qg, Qmax, Qmin, Vg, mBase, status, Pmax, Pmin
    ppc["gen"] = array([
        [1, 0, 0, 100, -100, 1.05, 100, 1, 100, 0],
        [2, 0.5, 0, 100, -100, 1.05, 100, 1, 100, 0]
    ])

    ppc["gen"][:, 1] = ppc["gen"][:, 1] * ppc["baseMVA"]

    ## branch data
    # fbus, tbus, r, x, b, rateA, rateB, rateC, ratio, angle, status
    ppc["branch"] = array([
        [1, 4, 0.020, 0.185, 0.009, 999, 100, 100, 0, 0, 1],
        [1, 6, 0.031, 0.259, 0.010, 999, 100, 100, 0, 0, 1],
        [2, 3, 0.006, 0.025, 0, 999, 100, 100, 0, 0, 1],
        [2, 5, 0.071, 0.320, 0.015, 999, 100, 100, 0, 0, 1],
        [4, 6, 0.024, 0.204, 0.010, 999, 100, 100, 0, 0, 1],
        [3, 4, 0.075, 0.067, 0, 999, 100, 100, 0, 0, 1],
        [5, 6, 0.025, 0.150, 0.017, 999, 100, 100, 0, 0, 1]
    ])

    #ppc["branch"][:, 2] = ppc["branch"][:, 2] * 1.75

    return ppc
