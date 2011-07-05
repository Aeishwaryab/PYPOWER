# Copyright (C) 1996-2011 Power System Engineering Research Center
# Copyright (C) 2010-2011 Richard Lincoln
#
# PYPOWER is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License,
# or (at your option) any later version.
#
# PYPOWER is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PYPOWER. If not, see <http://www.gnu.org/licenses/>.

import sys

from numpy import array, zeros, ones, ceil, arange, cumsum, r_, c_, ix_, any
from numpy import logical_and, append, flatnonzero as find

from pypower.isload import isload

from pypower.idx_cost import NCOST, COST, PW_LINEAR, STARTUP, SHUTDOWN, MODEL
from pypower.idx_gen import PMIN, PMAX, QMIN, QMAX, GEN_STATUS

from pypower.extras.smartmarket.pricelimits import pricelimits


def off2case(gen, gencost, offers, bids=None, lim=None):
    """Updates case variables gen & gencost from quantity & price offers.

    Updates C{gen} & C{gencost} variables based on the C{offers} and C{bids}
    supplied, where each is a dict (or C{bids} can be an empty dict) with
    field 'P' (active power offer/bid) and optional field 'Q' (reactive power
    offer/bid), each of which is another struct with fields 'qty' and 'prc',
    m x n matrices of quantity and price offers/bids, respectively. There are
    m offers with n blocks each.
    For C{offers}, m can be equal to the number of actual generators (not
    including dispatchable loads) or the total number of rows in the C{gen}
    matrix (including dispatchable loads). For C{bids}, m can be equal to the
    number of dispatchable loads or the total number of rows in the C{gen}
    matrix. Non-zero offer (bid) quantities for C{gen} matrix entries where
    Pmax <= 0 (Pmin >= 0) produce an error. Similarly for Q.

    E.g.
        offers.P.qty - m x n, active power quantity offers, m offers, n blocks
                .prc - m x n, active power price offers
              .Q.qty - m x n, reactive power quantity offers
                .prc - m x n, reactive power price offers

    These values are used to update PMIN, PMAX, QMIN, QMAX and GEN_STATUS
    columns of the GEN matrix and all columns of the GENCOST matrix except
    STARTUP and SHUTDOWN.

    The last argument, C{lim} is a dict with the following fields,
    all of which are optional:
        lim.P.min_bid
             .max_offer
           .Q.min_bid
             .max_offer
    Any price offers (bids) for real power above (below) lim['P']['max_offer']
    (lim['P']['min_bid']) will be treated as being withheld. Likewise for Q.

    @see C{case2off}
    @see: U{http://www.pserc.cornell.edu/matpower/}
    """
    ## default args and stuff
    if bids == None:
        bids = array([])
    if lim == None:
        lim = {}

    if 'Q' in offers or 'Q' in bids:
        haveQ = 1
    else:
        haveQ = 0

    lim = pricelimits(lim, haveQ)
    if len(bids) == 0:
        np = offers['P']['qty'].shape[1]
        bids = { 'P': {'qty': zeros((0, np)), 'prc': zeros((0, np))} }

    if haveQ:
        if 'Q' not in bids:
            bids['Q'] = {'qty': array([]), 'prc': array([])}
        elif 'Q' not in offers:
            offers['Q'] = {'qty': array([]), 'prc': array([])}


    ## indices and sizes
    ngc = gencost.shape[1]
    G = find( ~isload(gen) )       ## real generators
    L = find(  isload(gen) )       ## dispatchable loads
    nGL = gen.shape[0]
    idxPo, idxPb, idxQo, idxQb = idx_vecs(offers, bids, G, L, haveQ)

    if haveQ:
        if gencost.shape[0] == nGL:
            ## set all reactive costs to zero if not provided
            gencost = c_[
                gencost,
                r_[PW_LINEAR * ones(nGL, 1), gencost[:,[STARTUP, SHUTDOWN]], 2 * ones((nGL, 1)), zeros((nGL, ngc - 4)) ]
            ]
            gencost[G + nGL, COST + 2] =  1
            gencost[L + nGL, COST]     = -1
        elif gencost.shape[0] != 2 * nGL:
            sys.stderr.write('gencost should have either %d or %d rows\n' % (nGL, 2 * nGL))


    ## number of points to define piece-wise linear cost
    if any( logical_and(idxPo, idxPb) ):
        np = offers['P']['qty'].shape[1] + bids['P']['qty'].shape[1]
    else:
        np = max([ offers['P']['qty'].shape[1], bids['P']['qty'].shape[1] ])

    if haveQ:
        if any( logical_and(idxQo, idxQb) ):
            np = max([ np, offers['Q']['qty'].shape[1] + bids['Q']['qty'].shape[1] ])
        else:
            np = max([ np, offers['Q']['qty'].shape[1], bids['Q']['qty'].shape[1] ])

    np = np + 1
    if any(idxPo + idxPb == 0):  ## some gens have no offer or bid, use original cost
        np = max([ np, ceil(ngc - (NCOST + 1)) / 2 ])

    ## initialize new cost matrices
    Pgencost            = zeros((nGL, (COST+1) + 2 * np - 1))
    Pgencost[:, MODEL]  = PW_LINEAR * ones(nGL)
    Pgencost[:, [STARTUP, SHUTDOWN]] = gencost[:nGL, [STARTUP, SHUTDOWN]]
    if haveQ:
        Qgencost = Pgencost.copy()
        Qgencost[:, [STARTUP, SHUTDOWN]] = gencost[ix_(nGL + arange(nGL), [STARTUP, SHUTDOWN])]

    for i in xrange(nGL):
        ## convert active power bids & offers into piecewise linear segments
        if idxPb[i]:     ## there is a bid for this unit
            if (gen[i, PMIN] >= 0) and any(bids['P']['qty'][idxPb[i] - 1, :]):
                sys.stderr.write('Pmin >= 0, bid not allowed for gen %d\n' % i)

            xxPb, yyPb, nPb = offbid2pwl(bids['P']['qty'][idxPb[i] - 1, :], bids['P']['prc'][idxPb[i] - 1, :], 1, lim['P']['min_bid'])
        else:
            nPb = 0

        if idxPo[i]:     ## there is an offer for this unit
            if (gen[i, PMAX] <= 0) and any(offers['P']['qty'][idxPo[i] - 1, :]):
                sys.stderr.write('Pmax <= 0, offer not allowed for gen %d\n' % i)

            xxPo, yyPo, nPo = offbid2pwl(offers['P']['qty'][idxPo[i] - 1, :], offers['P']['prc'][idxPo[i] - 1, :], 0, lim['P']['max_offer'])
        else:
            nPo = 0

        ## convert reactive power bids & offers into piecewise linear segments
        if haveQ:
            if idxQb[i]:     ## there is a bid for this unit
                if (gen[i, QMIN] >= 0) and any(bids['Q']['qty'][idxQb[i] - 1, :]):
                    sys.stderr.write('Qmin >= 0, reactive bid not allowed for gen %d\n' % i)

                xxQb, yyQb, nQb = offbid2pwl(bids['Q']['qty'][idxQb[i] - 1, :], bids['Q']['prc'][idxQb[i] - 1, :], 1, lim['Q']['min_bid'])
            else:
                nQb = 0

            if idxQo[i]:     ## there is an offer for this unit
                if (gen[i, QMAX] <= 0) and any(offers['Q']['qty'][idxQo[i], :]):
                    sys.stderr.write('Qmax <= 0, reactive offer not allowed for gen %d\n' % i)

                xxQo, yyQo, nQo = offbid2pwl(offers['Q']['qty'][idxQo[i] - 1, :], offers['Q']['prc'][idxQo[i] - 1, :], 0, lim['Q']['max_offer'])
            else:
                nQo = 0
        else:
            nQb = 0
            nQo = 0

        ## collect the pwl segments for active power
        if (nPb > 1) and (nPo > 1):           ## bid and offer (positive and negative qtys)
            if xxPb[-1] or yyPb[-1] or xxPo[0] or yyPo[0]:
                sys.stderr.write('Oops ... these 4 numbers should be zero: %g %g %g %g\n' % \
                    (xxPb[-1], yyPb[-1], xxPo[0], yyPo[0]))

            xxP = r_[xxPb, xxPo[1:]]
            yyP = r_[yyPb, yyPo[1:]]
            npP = nPb + nPo - 1
        elif (nPb <= 1) and (nPo > 1): ## offer only
            xxP = xxPo.copy()
            yyP = yyPo.copy()
            npP = nPo
        elif (nPb > 1) and (nPo <= 1): ## bid only
            xxP = xxPb.copy()
            yyP = yyPb.copy()
            npP = nPb
        else:
            npP = 0

        ## collect the pwl segments for reactive power
        if (nQb > 1) and (nQo > 1):           ## bid and offer (positive and negative qtys)
            if xxQb[-1] or yyQb[-1] or xxQo[0] or yyQo[0]:
                sys.stderr.write('Oops ... these 4 numbers should be zero: %g %g %g %g\n' % \
                    (xxQb[-1], yyQb[-1], xxQo[0], yyQo[0]))

            xxQ = r_[xxQb, xxQo[1:]]
            yyQ = r_[yyQb, yyQo[1:]]
            npQ = nQb + nQo - 1
        elif (nQb <= 1) and (nQo > 1):  ## offer only
            xxQ = xxQo.copy()
            yyQ = yyQo.copy()
            npQ = nQo
        elif (nQb > 1) and (nQo <= 1):  ## bid only
            xxQ = xxQb.copy()
            yyQ = yyQb.copy()
            npQ = nQb
        else:
            npQ = 0

        ## initialize new gen limits
        Pmin = gen[i, PMIN]
        Pmax = gen[i, PMAX]
        Qmin = gen[i, QMIN]
        Qmax = gen[i, QMAX]

        ## update real part of gen and gencost
        if npP:
            ## update gen limits
            if gen[i, PMAX] > 0:
                Pmax = max(xxP)
                if (Pmax < gen[i, PMIN]) or (Pmax > gen[i, PMAX]):
                    sys.stderr.write('offer quantity (%g) must be between max(0,PMIN) (%g) and PMAX (%g)\n' %
                        (Pmax, max([0, gen[i, PMIN]]), gen[i, PMAX]))

            if gen[i, PMIN] < 0:
                Pmin = min(xxP)
                if (Pmin >= gen[i, PMIN]) and (Pmin <= gen[i, PMAX]):
                    if isload(gen[i, :]):
                        Qmin = gen[i, QMIN] * Pmin / gen[i, PMIN]
                        Qmax = gen[i, QMAX] * Pmin / gen[i, PMIN]
                else:
                    sys.stderr.write('bid quantity (%g) must be between max(0,-PMAX) (%g) and -PMIN (%g)\n' %
                        (-Pmin, max([0, -gen[i, PMAX]]), -gen[i, PMIN]))

            ## update gencost
            Pgencost[i, NCOST] = npP
            Pgencost[i,      COST:( (COST + 1) + 2*npP - 2 ):2] = xxP
            Pgencost[i,  (COST+1):( (COST + 1) + 2*npP - 1 ):2] = yyP
        else:
            ## no capacity bid/offered for active power
            if npQ and ~isload(gen[i, :]) and (gen[i, PMIN] <= 0) and (gen[i, PMAX] >= 0):
                ## but we do have a reactive bid/offer and we can dispatch
                ## at zero real power without shutting down
                Pmin = 0
                Pmax = 0
                Pgencost[i, :ngc] = gencost[i, :ngc]
            else:            ## none for reactive either
                ## shut down the unit
                gen[i, GEN_STATUS] = 0


        ## update reactive part of gen and gencost
        if npQ:
            ## update gen limits
            if gen[i, QMAX] > 0:
                Qmax = min([ Qmax, max(xxQ) ])
                if (Qmax >= gen[i, QMIN]) and (Qmax <= gen[i, QMAX]):
                    if isload(gen[i, :]):
                        Pmin = gen[i, PMIN] * Qmax / gen[i, QMAX]
                else:
                    sys.stderr.write('reactive offer quantity (%g) must be between max(0,QMIN) (%g) and QMAX (%g)' %
                        (Qmax, max([0, gen[i, QMIN]]), gen[i, QMAX]))

            if gen[i, QMIN] < 0:
                Qmin = max([ Qmin, min(xxQ) ])
                if (Qmin >= gen[i, QMIN]) and (Qmin <= gen[i, QMAX]):
                    if isload(gen[i, :]):
                        Pmin = gen[i, PMIN] * Qmin / gen[i, QMIN]
                else:
                    sys.stderr.write('reactive bid quantity (%g) must be between max(0,-QMAX) (%g) and -QMIN (%g)' %
                        (-Qmin, max([0, -gen[i, QMAX]]), -gen[i, QMIN]))


            ## update gencost
            Qgencost[i, NCOST] = npQ
            Qgencost[i,      COST:( (COST+1) + 2*npQ - 2 ):2] = xxQ
            Qgencost[i,  (COST+1):( (COST+1) + 2*npQ - 1 ):2] = yyQ
        else:
            ## no capacity bid/offered for reactive power
            if haveQ:
                if npP and (gen[i, QMIN] <= 0) and (gen[i, QMAX] >= 0):
                    ## but we do have an active bid/offer and we might be able to
                    ## dispatch at zero reactive power without shutting down
                    if isload(gen[i, :]) and (gen[i, QMAX] > 0) or (gen[i, QMIN] < 0):
                        ## load w/non-unity power factor, zero Q => must shut down
                        gen[i, GEN_STATUS] = 0
                    else:    ## can dispatch at zero reactive without shutting down
                        Qmin = 0
                        Qmax = 0

                    Qgencost[i, :ngc] = gencost[nGL + i, :ngc]
                else:            ## none for reactive either
                    ## shut down the unit
                    gen[i, GEN_STATUS] = 0


        if gen[i, GEN_STATUS]:       ## running
            gen[i, PMIN] = Pmin    ## update limits
            gen[i, PMAX] = Pmax
            gen[i, QMIN] = Qmin
            gen[i, QMAX] = Qmax
        else:                        ## shut down
            ## do not modify cost
            # append columns if necessary
            if Pgencost.shape[1] < gencost.shape[1]:
                ncol = gencost.shape[1] - Pgencost.shape[1]
                Pgencost = append(Pgencost, zeros((nGL, ncol)), 1)

            Pgencost[i, :ngc] = gencost[i, :ngc]
            if haveQ:
                # append columns if necessary
                if Qgencost.shape[1] < gencost.shape[1]:
                    ncol = gencost.shape[1] - Qgencost.shape[1]
                    Qgencost = append(Qgencost, zeros((nGL, ncol)), 1)

                Qgencost[i, :ngc] = gencost[nGL + i, :ngc]


    if not haveQ:
        Qgencost = zeros((0, Pgencost.shape[1]))

    np = max(r_[ Pgencost[:, NCOST], Qgencost[:, NCOST] ])
    ngc = NCOST + 1 + 2 * np
    gencost = r_[ Pgencost[:, :ngc], Qgencost[:, :ngc] ]

    return gen, gencost


def offbid2pwl(qty, prc, isbid, lim=None):

    if any(qty < 0):
        sys.stderr.write('offer/bid quantities must be non-negative\n')

    ## strip zero quantities and optionally strip prices beyond lim
    if lim == None:
        valid = find(qty)
    else:
        if isbid:
            valid = find( logical_and(qty, prc) >= lim)
        else:
            valid = find( logical_and(qty, prc) <= lim)

    if isbid:
        n = len(valid)
        qq = qty[valid[n:0:-1]]    ## row vector of quantities
        pp = prc[valid[n:0:-1]]    ## row vector of prices
    else:
        qq = qty[valid]            ## row vector of quantities
        pp = prc[valid]            ## row vector of prices

    n = len(qq) + 1                ## number of points to define pwl function

    ## form piece-wise linear total cost function
    if n > 1:       ## otherwise, leave all cost info zero (specifically NCOST)
        xx = array([0, cumsum(qq)])
        yy = array([0, cumsum(pp * qq)])
        if isbid:
            xx = xx - xx[-1]
            yy = yy - yy[-1]
    else:
        xx = array([])
        yy = array([])

    return xx, yy, n


##-----  idx_vecs()  -----
def idx_vecs(offers, bids, G, L, haveQ):

    nG = len(G)
    nL = len(L)
    nGL = nG + nL

    idxPo = zeros(nGL, int)
    idxPb = zeros(nGL, int)
    idxQo = zeros(nGL, int)
    idxQb = zeros(nGL, int)

    ## numbers of offers/bids submitted
    nPo = offers['P']['qty'].shape[0]
    nPb = bids['P']['qty'].shape[0]
    if haveQ:
        nQo = offers['Q']['qty'].shape[0]
        nQb = bids['Q']['qty'].shape[0]

    ## make sure dimensions of qty and prc offers/bids match
    if offers['P']['qty'].shape != offers['P']['prc'].shape:
        sys.stderr.write('dimensions of offers[\'P\'][\'qty\'] (%d x %d) and offers[\'P\'][\'prc\'] (%d x %d) do not match' %
            offers['P']['qty'].shape, offers['P']['prc'].shape)

    if bids['P']['qty'].shape != bids['P']['prc'].shape:
        sys.stderr.write('dimensions of bids[\'P\'][\'qty\'] (%d x %d) and bids[\'P\'][\'prc\'] (%d x %d) do not match' %
            bids['P']['qty'].shape, bids['P']['prc'].shape)

    if haveQ:
        if offers['Q']['qty'].shape != offers['Q']['prc'].shape:
            sys.stderr.write('dimensions of offers[\'Q\'][\'qty\'] (%d x %d) and offers[\'Q\'][\'prc\'] (%d x %d) do not match' %
                offers['Q']['qty'].shape, offers['Q']['prc'].shape)

        if bids['Q']['qty'].shape != bids['Q']['prc'].shape:
            sys.stderr.write('dimensions of bids[\'Q\'][\'qty\'] (%d x %d) and bids[\'Q\'][\'prc\'] (%d x %d) do not match' %
                bids['Q']['qty'].shape, bids['Q']['prc'].shape)


    ## active power offer indices
    if nPo == nGL:
        idxPo = arange(nGL) + 1
    elif nPo == nG:
        idxPo[G] = arange(nG) + 1
    elif nPo != 0:
        sys.stderr.write('number of active power offers must be zero or match either the number of generators or the total number of rows in gen\n')

    ## active power bid indices
    if nPb == nGL:
        idxPb = arange(nGL) + 1
    elif nPb == nL:
        idxPb[L] = arange(nL) + 1
    elif nPb != 0:
        sys.stderr.write('number of active power bids must be zero or match either the number of dispatchable loads or the total number of rows in gen\n')

    if haveQ:
        ## reactive power offer indices
        if nQo == nGL:
            idxQo = arange(nGL) + 1
        elif nQo == nG:
            idxQo[G] = arange(nG) + 1
        elif nQo != 0:
            sys.stderr.write('number of reactive power offers must be zero or match either the number of generators or the total number of rows in gen\n')

        ## reactive power bid indices
        if nQb == nGL:
            idxQb = arange(nGL) + 1
        elif nQb != 0:
            sys.stderr.write('number of reactive power bids must be zero or match the total number of rows in gen\n')

    return idxPo, idxPb, idxQo, idxQb
