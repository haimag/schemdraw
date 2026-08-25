''' Define wave types and transitions for logic timing diagrams '''

from __future__ import annotations
from typing import Sequence
import math

from .. import util
from ..segments import Segment, SegmentPoly, SegmentText, SegmentType

def _state_level(state: str, prev: bool = False) -> str:
    ''' Get level of wave state (0, 1, V, z, -).
        Local copy to avoid circular import with timing.py.
    '''
    if state in 'c' and prev:
        return '0'
    if state in 'c':
        return '1'
    if state in 'C' and prev:
        return '1'
    if state in 'C':
        return '0'
    if state in '23456789=xb':
        return 'V'
    if state in '1unNhHiwWI':
        return '1'
    if state in '0dpPlLqvVQ':
        return '0'
    if state in 'e':
        return '-'
    if state in 'z-':
        return state
    return state

def expcurve(height: float) -> tuple[Sequence[float], Sequence[float]]:
    ''' Exponential decay curve (for u/d waveforms) '''
    xcurve = util.linspace(0, 1, 10)
    ycurve = [height * math.exp(-v*6) for v in xcurve]
    return xcurve, ycurve


def diffarrow(xcross: float, rise: float, y0: float, y1: float, kwargs: dict) -> Segment:
    ''' Get an arrow at a differential crossing point (xcross, yhalf),
        pointing along the slope of the rise transition. The arrowhead's
        centroid is at the crossing, and its direction matches the slope
        so it stays on the line segment for any configured rise time.
    '''
    height = y1 - y0
    line_length = math.hypot(rise, height)
    arrowlength = min(.25, .75*line_length)
    arrowwidth = .12
    yhalf = (y0 + y1)/2
    dx = rise / line_length
    dy = height / line_length
    crossing = (xcross, yhalf)
    head = (crossing[0] + dx*arrowlength*2/3,
            crossing[1] + dy*arrowlength*2/3)
    tail = (crossing[0] - dx*arrowlength/3,
            crossing[1] - dy*arrowlength/3)
    return Segment([tail, head], arrow='->', arrowwidth=arrowwidth,
                   arrowlength=arrowlength, **kwargs)


def _complement_plevel(plevel: str) -> str:
    ''' Get the level of the dashed (S-) line from the level of the
        solid (S+) line: the complement of a high or low level, or the
        level itself for undefined states (z, V) and empty (-) states.
    '''
    return {'0': '1', '1': '0'}.get(plevel, plevel)

def _isdiff(state: str) -> bool:
    '''Return True if the state is a differential signal state. '''
    return state in 'wvWVqiQI'

def _diff_line_level(state: str, is_top: bool) -> str:
    ''' Get the level of a specific line (top or bottom) for a differential signal state.

        For S+-on-top states (w, W, q, Q): S+ (solid) is top at level 1,
        S- (dashed) is bottom at level 0.
        For S+-on-bottom states (v, V, i, I): S+ (solid) is bottom at level 0,
        S- (dashed) is top at level 1.
    '''
    spl = _state_level(state, prev=False) # S+ level
    sml = _complement_plevel(spl)         # S- level
    if state in 'wvWV':
        # w/W: top=S+(solid), bottom=S-(dashed)
        # v/V: top=S-(dashed), bottom=S+(solid)
        return spl if (state in 'wW') == is_top else sml
    elif state in 'qiQI':
        return spl if (state in 'qQ') == is_top else sml
    return spl # fallback

def _line_prev_level(pstate: str, plevel: str, is_top: bool) -> str:
    ''' Get this line's level from the previous state.

    For a previous non-differential state, both lines had the same
    level (plevel). For a previous differential state, each line
    had its own independent level.
    '''
    if _isdiff(pstate):
        return _diff_line_level(pstate, is_top)
    else:
        return plevel

def _line_next_level(nstate: str, nlevel: str, is_top: bool) -> str:
    ''' Get this line's level for the next state.

    For a next non-differential state, both lines will have the same
    level (nlevel). For a next differential state, each line will
    have its own independent level.
    '''
    if _isdiff(nstate):
        return _diff_line_level(nstate, is_top)
    else:
        return nlevel


def getsplit(x0: float, y0: float, y1: float, **kwargs) -> list:
    ''' Get segments for a split, based on double-sigmoid. Splits are filled
        with background color to hide whatever's underneath.
    '''
    sig = Doublesigmoid(x0, y0, y1, **kwargs)
    leftx, lefty = sig.curve(side='left')
    rghtx, rghty = sig.curve(side='right')
    left = list(zip(leftx, lefty))
    right = list(zip(rghtx, rghty))
    segments = [Segment(left, lw=1, zorder=3),
                Segment(right, lw=1, zorder=3),
                SegmentPoly(left+right[::-1], zorder=3, color='none',
                            fill='bg', lw=1, closed=False)]
    return segments


class Doublesigmoid:
    ''' Create a double sigmoid - used for "break" symbol in timing diagrams

        Args:
            x0: Center x position
            y0: Bottom y position
            y1: Top y position
            extend: Amount to extend the sigmoid over/under the y0 & y1 position
            gap: Separation between the two sigmoids
    '''
    def __init__(self, x0: float, y0: float, y1: float,
                 extend: float = 0.1, gap: float = 0.2, **kwargs):
        self.x0 = x0  # Center
        self.y0 = y0
        self.y1 = y1
        self.extend = extend  # Over/under y0 and y1 lines, relative to height
        self.gap = gap  # Distance from first to second curve, relative to height
        self.kwargs = kwargs

        self.rate = 25  # Adjust curvature
        self.height = self.y1-self.y0
        self.curve1x = self.x0 - self.gap*self.height/2
        self.curve2x = self.x0 + self.gap*self.height/2
        self.top = self.y1 + self.height * self.extend
        self.bot = self.y0 - self.height * self.extend

    def segments(self) -> Sequence[SegmentType]:
        ''' Get segments for this wave section '''
        segments = []
        x, y = self.curve(side='left')
        segments.append(Segment(list(zip(x, y)), **self.kwargs))
        x, y = self.curve(side='right')
        segments.append(Segment(list(zip(x, y)), **self.kwargs))
        return segments

    def curve(self, side: str = 'left', crop: bool = False,
              ofst: float = 0) -> tuple[Sequence[float], Sequence[float]]:
        ''' Get sigmoid curve points

            Args:
                side: left or right
                crop: whether to crop the top/bottom at y0 and y1
                ofst: X offset
        '''
        fullh = self.height * (1 + self.extend*2)
        drop = self.height * self.extend

        # Base sigmoid
        sigx = util.linspace(-0.15, 0.15)
        sigy = [1/(1+math.exp(-x*self.rate)) * fullh - drop for x in sigx]

        if crop:
            sigx = [x for i, x in enumerate(sigx) if 0 <= sigy[i] < self.height]
            sigy = [y for i, y in enumerate(sigy) if 0 <= sigy[i] < self.height]

        # Move to position
        x0 = self.curve1x if side == 'left' else self.curve2x
        sigx = [x+x0+ofst for x in sigx]
        sigy = [y+self.y0 for y in sigy]
        return sigx, sigy


class Wave0:
    ''' Wave section in low state - `0` '''
    def __init__(self, params):
        self.params = params
        self.x0 = self.params.get('x0', 0)
        self.xend = self.params.get('xend', 1)
        self.y0 = self.params.get('y0', 0)
        self.y1 = self.params.get('y1', .5)
        self.y1_prev = self.params.get('y1_prev', .5)
        self.state = self.params.get('state', '0')
        self.pstate = self.params.get('pstate', '-')
        self.nstate = self.params.get('nstate', '-')
        self.plevel = self.params.get('plevel', '-')
        self.nlevel = self.params.get('nlevel', '-')
        self.rise = self.params.get('rise', 0.1)
        self.xrise = self.x0 + self.rise
        self.xrisehalf = self.x0 + self.rise / 2
        self.yhalf = (self.y0 + self.y1)/2
        self.xcenter = (self.x0 + self.xend)/2
        self.xtext = self.xcenter + self.rise / 2
        self.kwargs = self.params.get('kwargs', {'lw': 1})

    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        verts = {
            '-': [(self.x0, self.y0)],
            '0': [(self.x0, self.y0), (self.xrisehalf, self.yhalf), (self.xrise, self.y0)] if self.pstate in '0lL' else [(self.x0, self.y0)],
            '1': [(self.x0, self.y1), (self.xrise, self.y0)],
            'z': [(self.x0, self.yhalf), (self.xrisehalf, self.y0)],
            'V': [(self.xrise, self.y0)],
        }.get(self.plevel, [])
        return verts

    def verts_out(self) -> list[tuple[float, float]]:
        ''' Get vertices for output transition '''
        return [(self.xend, self.y0)]

    def segments(self) -> list[SegmentType]:
        ''' Get segments for this wave section '''
        verts = self.verts_in() + self.verts_out()
        if verts:
            return [Segment(verts, **self.kwargs)]
        return []


class WaveL(Wave0):
    ''' Wave section in low state with no transition, and arrow if
        capital L (`l` or `L`)
    '''
    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        if self.params['pstate'] in 'pP' or self.plevel == 'V':
            return [(self.x0, self.y0)]
        elif _isdiff(self.pstate) and self.plevel == '0':
            return [(self.x0, self.y0)]
        elif _isdiff(self.pstate) and self.plevel == '1':
            return [(self.xrise, self.y0)]
        else:
            return [(self.x0, self.y1), (self.x0, self.y0)]

    def segments(self) -> list[SegmentType]:
        ''' Get segments for this wave section '''
        segments = super().segments()
        if self.state == 'L' and not _isdiff(self.pstate):
            alength = .25
            awidth = .12
            yhead = self.yhalf - alength/3*2
            ytail = self.yhalf + alength/3
            segments.append(Segment([(self.x0, ytail), (self.x0, yhead)],
                                    arrow='->', arrowwidth=awidth, arrowlength=alength, **self.kwargs))
        return segments


class Wave1(Wave0):
    ''' Wave section in high state - `1` '''
    def verts_in(self):
        ''' Get vertices for input transition '''
        v1 = [(self.x0, self.y1_prev), (self.xrisehalf, self.yhalf), (self.xrise, self.y1)] if self.pstate in '1hH' else [(self.x0, self.y1)]
        if self.pstate in '1hH':
            if self.y1_prev != self.y1:
                v1 = [(self.x0, self.y1_prev), (self.xrise, self.y1)]
            else:
                v1 = [(self.x0, self.y1), (self.xrisehalf, self.yhalf), (self.xrise, self.y1)]
        else:
            v1 = [(self.x0, self.y1)]


        verts = {'-': [(self.x0, self.y1)],
                 '0': [(self.x0, self.y0), (self.xrise, self.y1)],
                 '1': v1,
                 'z': [(self.x0, self.yhalf), (self.xrisehalf, self.y1)],
                 'V': [(self.xrise, self.y1)] if self.pstate not in 'b' else [(self.x0, self.y1)],
                 }.get(self.plevel, [])
        return verts

    def verts_out(self) -> list[tuple[float, float]]:
        ''' Get vertices for output transition '''
        return [(self.xend, self.y1)]


class WaveH(Wave1):
    ''' Wave section in high state with no transition, and arrow if
        capital H (`h` or `H`)
    '''
    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        if self.params['pstate'] in 'nN' or self.plevel == 'V':
            return [(self.x0, self.y1)]
        elif _isdiff(self.pstate) and self.plevel == '1':
            return [(self.x0, self.y1)]
        elif _isdiff(self.pstate) and self.plevel == '0':
            return [(self.xrise, self.y1)]
        else:
            return [(self.x0, self.y0), (self.x0, self.y1)]

    def segments(self) -> list[SegmentType]:
        ''' Get segments for this wave section '''
        segments = super().segments()
        if self.state == 'H' and not _isdiff(self.pstate):
            alength = .25
            awidth = .12
            ytail = self.yhalf - alength/3
            yhead = self.yhalf + alength/3*2
            segments.append(Segment([(self.x0, ytail), (self.x0, yhead)],
                                    arrow='->', arrowwidth=awidth, arrowlength=alength, **self.kwargs))
        return segments


class Wavez(Wave0):
    ''' Wave section in high-impedance state (halfway up) (`z`) '''
    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        xcurve, yexp = expcurve((self.y1-self.y0)/2)
        ycurve = [self.yhalf + yc for yc in yexp]
        ycurveflip = [self.yhalf - yc for yc in yexp]
        xcurve = [self.x0+xc*self.rise*6 for xc in xcurve]
        verts = {'-': [(self.x0, self.yhalf)],
                 '0': list(zip(xcurve, ycurveflip)) if self.pstate not in 'iqIQ' else [(self.xrisehalf, self.yhalf)],
                 '1': list(zip(xcurve, ycurve)) if self.pstate not in 'iqIQ' else [(self.xrisehalf, self.yhalf)],
                 'z': [(self.x0, self.yhalf)],
                 'V': [(self.xrisehalf, self.yhalf)] if self.pstate in 'b' else [(xcurve[-1], self.yhalf)],
                 }.get(self.plevel, [])
        if self.pstate in 'wvWV':
            if self.plevel in '-0':
                verts = [(self.x0, self.y0), (self.x0+self.rise/2, self.yhalf)]
            else:
                verts = [(self.x0, self.y1), (self.x0+self.rise/2, self.yhalf)]
        return verts

    def verts_out(self) -> list[tuple[float, float]]:
        ''' Get vertices for output transition '''
        return [(self.xend, self.yhalf)]


class WaveV(Wave0):
    ''' Wave section in data state (block) - `=23456789X` '''
    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        verts = {'-': [(self.x0, self.y1), (self.x0, self.y0)],
                 '0': [(self.xrise, self.y1), (self.x0, self.y0)],
                 '1': [(self.x0, self.y1), (self.xrise, self.y0)],
                 'z': [(self.xrise, self.y1), (self.xrisehalf, self.yhalf),
                       (self.x0, self.yhalf), (self.xrisehalf, self.yhalf),
                       (self.xrise, self.y0)],  # CCW
                 'V': [(self.xrise, self.y1), (self.xrisehalf, self.yhalf),
                       (self.xrise, self.y0)],  # CCW
                 }.get(self.plevel, [])
        return verts

    def verts_out(self) -> list[tuple[float, float]]:
        ''' Get vertices for output transition '''
        xcurve, yexp = expcurve((self.y1-self.y0))
        xcurve = [self.xend+xc*self.rise*6 for xc in xcurve]
        ycurveh = [self.y0+yc/2 for yc in yexp]   # Half exp fall
        ycurvehf = [self.y1-yc/2 for yc in yexp]  # Flipped half
        verts = {
            '0': [(self.xend+self.rise, self.y0), (self.xend, self.y1)],  # Fall
            '1': [(self.xend, self.y0), (self.xend+self.rise, self.y1)],  # Rise
            'z': (list(zip(xcurve, [yc-(self.y1-self.y0)/2 for yc in ycurvehf])) +
                  list(zip(xcurve[::-1], [yc+(self.y1-self.y0)/2 for yc in ycurveh[::-1]]))),
            'V': [(self.xend, self.y0), (self.xend+self.rise/2, self.yhalf), (self.xend, self.y1)],
            '-': [(self.xend, self.y0), (self.xend, self.y1)],
        }.get(self.nlevel, [])
        return verts

    def fillcolor(self):
        ''' Get color to fill '''
        fill = {'3': '#feffc2',
                '4': '#ffe2ba',
                '5': '#abd9ff',
                '6': '#bdfbff',
                '7': '#bdffcb',
                '8': '#e3a5fa',
                '9': '#f7b7bd'}.get(self.params.get('state', '2'), None)
        ukwargs = self.kwargs.copy()
        ukwargs['fill'] = fill
        return ukwargs

    def segments(self) -> list[SegmentType]:
        ''' Get segments for this wave section '''
        ukwargs = self.fillcolor()
        if self.state == 'x':
            ukwargs['hatch'] = True

        segments: list[SegmentType] = []
        if self.nstate in '-|' and self.pstate in '-|':  # Open both ends. Draw two lines and a poly
            ukwargs['color'] = 'none'
            segments.append(Segment([(self.x0, self.y0), (self.xend, self.y0)], **self.kwargs))
            segments.append(Segment([(self.x0, self.y1), (self.xend, self.y1)], **self.kwargs))
            segments.append(SegmentPoly([(self.x0, self.y0), (self.xend, self.y0),
                                         (self.xend, self.y1), (self.x0, self.y1)], **ukwargs))
        elif self.pstate in '-|':  # Open left end
            segments.append(SegmentPoly(
                [(self.x0, self.y0)] + self.verts_out() + [(self.x0, self.y1)],
                closed=False, **ukwargs))

        elif self.nstate in '-|':  # Open right end
            segments.append(
                SegmentPoly([(self.xend, self.y1)] + self.verts_in() + [(self.xend, self.y0)],
                            closed=False, **ukwargs))

        else:
            segments.append(SegmentPoly(self.verts_in()+self.verts_out(), **ukwargs))

        if self.params.get('data', None) and self.params.get('state', None) != 'x':
            segments.append(SegmentText((self.xtext, self.yhalf), self.params['data'][0],
                                        color=self.params['datacolor'],
                                        fontsize=self.params['datasize'], align=('center', 'center')))
            self.params['data'].pop(0)
        return segments


class WaveU(Wave1):
    ''' Wave section high state with pullup curve (`u`) '''
    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        xcurve, yexp = expcurve((self.y1-self.y0))
        xcurve = [self.x0+xc*self.rise*6 for xc in xcurve]
        ycurvef = [self.y1-yc for yc in yexp]     # Flipped
        ycurvehf = [self.y1-yc/2 for yc in yexp]  # Flipped half
        verts = {'-': [(self.x0, self.y1)],
                 '0': list(zip(xcurve, ycurvef)),
                 '1': [(self.x0, self.y1)],
                 'z': list(zip(xcurve, ycurvehf)),
                 'V': [(self.xrise, self.y1)],   # V gets the curve on output
                 }.get(self.plevel, [])
        return verts

    def segments(self) -> list[SegmentType]:
        ''' Get segments for this wave section '''
        verts = self.verts_in()
        segments: list[SegmentType] = [
            Segment(verts, **self.kwargs),
            Segment([verts[-1], (self.xend, self.y1)], ls=':', **self.kwargs)]
        return segments


class WaveD(Wave0):
    ''' Wave section low state with pull-down curve (`d`) '''
    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        xcurve, yexp = expcurve((self.y1-self.y0))
        xcurve = [self.x0+xc*self.rise*6 for xc in xcurve]
        ycurve = [self.y0+yc for yc in yexp]     # Exp fall
        ycurveh = [self.y0+yc/2 for yc in yexp]  # Half exp fall
        verts = {'-': [(self.x0, self.y0)],
                 '0': [(self.x0, self.y0)],
                 '1': list(zip(xcurve, ycurve)),
                 'z': list(zip(xcurve, ycurveh)),
                 'V': [(self.x0, self.y0)],
                 }.get(self.plevel, [])
        return verts

    def segments(self) -> list[SegmentType]:
        ''' Get segments for this wave section '''
        verts = self.verts_in()
        segments: list[SegmentType] = [
            Segment(verts, **self.kwargs),
            Segment([verts[-1], (self.xend, self.y0)], ls=':', **self.kwargs)]
        return segments


class WaveClk(Wave0):
    ''' Clock wave section (`n` `N` `p` `P`) '''
    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        state = self.state
        period = self.params['period']
        yh, yl = self.y1, self.y0
        if state in 'nN':
            yh, yl = yl, yh

        verts = []
        for p in range(self.params['periods']):
            verts.extend([(self.x0+period*p, yl), (self.x0+period*p, yh),
                          (self.x0+period*p+period/2, yh),
                          (self.x0+period*p+period/2, yl)])
        if (state in 'nN' and self.plevel in '0V') or state in 'pP' and self.plevel in '1V':
            verts = verts[1:]  # No blip at beginning
        return verts

    def verts_out(self) -> list[tuple[float, float]]:
        ''' Get vertices for output transition '''
        yh, yl = self.y1, self.y0
        if self.state in 'nN':
            yh, yl = yl, yh
        return [(self.xend, yl)]

    def segments(self) -> list[SegmentType]:
        ''' Get segments for this wave section '''
        segments = super().segments()
        if self.state in 'NP':
            period = self.params['period']
            periods = self.params['periods']
            alength = .25
            awidth = .12
            yhead = self.yhalf - alength/3*2
            ytail = self.yhalf + alength/3
            if self.state == 'P':
                yhead = self.yhalf + alength/3*2
                ytail = self.yhalf - alength/3
            for p in range(periods):
                xcenter = self.x0 + period*p
                segments.append(Segment(
                    [(xcenter, ytail), (xcenter, yhead)], arrow='->',
                    arrowwidth=awidth, arrowlength=alength, **self.kwargs))
        return segments


class WaveC(Wave0):
    ''' Clock with rise time (c or C) '''
    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        period = self.params['period']
        verts = {
            '0': [(self.x0, self.y0)],
            '1': [(self.x0, self.y1)],
            'V': [(self.xrisehalf, self.yhalf)],
            'z': [(self.x0, self.yhalf)],
        }.get(self.plevel, [])
        for p in range(self.params['periods']):
            verts.extend([(self.x0+period*p, self.y0), (self.x0+period*p+self.rise, self.y1),
                          (self.x0+period*p+period/2, self.y1),
                          (self.x0+period*p+self.rise+period/2, self.y0)])
        if self.plevel in 'z1V':
            verts.pop(1)
        return verts

    def verts_out(self) -> list[tuple[float, float]]:
        ''' Get vertices for output transition '''
        verts = [(self.xend, self.y0)]
        return verts


class WaveCbar(Wave0):
    ''' Clock with rise time (c or C) '''
    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        period = self.params['period']
        yh, yl = self.y1, self.y0
        verts = {
            '0': [(self.x0, yl)],
            '1': [(self.x0, yh)],
            'V': [(self.xrisehalf, self.yhalf)],
            'z': [(self.x0, self.yhalf)],
        }.get(self.plevel, [])

        for p in range(self.params['periods']):
            verts.extend([(self.x0+period*p, yh), (self.x0+period*p+self.rise, yl),
                          (self.x0+period*p+period/2, yl),
                          (self.x0+period*p+self.rise+period/2, yh)])
        if self.plevel in 'z0V':
            verts.pop(1)
        return verts

    def verts_out(self) -> list[tuple[float, float]]:
        ''' Get vertices for output transition '''
        verts = [(self.xend, self.y1)]
        return verts


class WaveIQ(WaveC):
    ''' Differential Clock wave section 'q'/'i' or half-period bit '''

    dash_comp = True  # Check dashed-line transitions against the S- level

    def segments(self) -> list[SegmentType]:
        segments: list[SegmentType] = []
        w = WaveCbar(self.params)
        wd = None
        if self.dash_comp:
            dash_plevel = _complement_plevel(self.params['plevel']) if _isdiff(self.pstate) else self.params['plevel']
            wparams = dict(self.params, plevel=dash_plevel)
            wd = WaveC(wparams) if self.state in 'iI' else WaveCbar(wparams)
        dashed_kwargs = self.kwargs.copy()
        if self.state not in 'b':
            dashed_kwargs['ls'] = ':'
            dashed_kwargs['color'] = 'gray'
        if self.state in 'iI':
            # Uppercase state: solid is the Cbar pattern (falls at the
            # start, rises at the middle of each period)
            dash = wd if wd is not None else self
            verts = dash.verts_in() + dash.verts_out()
            if self.nstate in '1pPu':
                verts += [(self.xend+self.rise, self.y1)]
            segments.append(Segment(verts, **dashed_kwargs))
            segments.append(Segment(w.verts_in()+w.verts_out(), **self.kwargs))
        else:
            dash = wd if wd is not None else w
            verts = dash.verts_in() + dash.verts_out()
            if self.nstate in '0nNd':
                verts += [(self.xend+self.rise, self.y0)]
            segments.append(Segment(self.verts_in() + self.verts_out(), **self.kwargs))
            segments.append(Segment(verts, **dashed_kwargs))

        if self.nstate in 'qizQI' or (self.state == 'b' and self.nstate in 'bcC23456789x='):
            segments.append(Segment(
                [(self.xend, self.y1), (self.xend+self.rise/2, self.yhalf),
                 (self.xend, self.y0)], **self.kwargs))
        elif self.nstate in '0' and self.state == 'b':
            segments.append(Segment([(self.xend, self.y0), (self.xend+self.rise, self.y0)], **self.kwargs))

        if self.params.get('data', None):
            segments.append(SegmentText(
                (self.x0+self.rise/2+self.params['period']/4, self.yhalf), self.params['data'][0],
                color=self.params['datacolor'],
                fontsize=self.params['datasize'], align=('center', 'center')))
            self.params['data'].pop(0)
        if self.params.get('data', None):
            segments.append(SegmentText(
                (self.x0+self.rise/2+self.params['period']*0.75, self.yhalf), self.params['data'][0],
                color=self.params['datacolor'],
                fontsize=self.params['datasize'], align=('center', 'center')))
            self.params['data'].pop(0)

        return segments


class WaveIQa(WaveIQ):
    ''' Differential Clock (like q/i) with an arrow at the differential
        crossing where the solid line transitions from low to high.
    '''

    dash_comp = True
    def arrows(self) -> list[Segment]:
        ''' Get arrows at the crossings of the differential clock, where
            the solid line goes from low to high. Returns an empty list
            if there are no low-to-high transitions in this section.
        '''
        period = self.params['period']
        periods = self.params['periods']
        if self.state in 'Q':
            # Solid (S+) rises at the start of each period, except the
            # first, where the rise was skipped if S+ was already high
            start = 0 if self.plevel in '0V-' else 1
            crossings = [self.x0 + p*period + self.rise/2
                         for p in range(start, periods)]
        else:
            # Solid (S+) rises at the middle of each period
            crossings = [self.x0 + p*period + period/2 + self.rise/2
                         for p in range(periods)]
        return [diffarrow(x, self.rise, self.y0, self.y1, self.kwargs)
                for x in crossings]

    def segments(self) -> list[SegmentType]:
        ''' Get segments for this wave section '''
        segments = super().segments()
        segments.extend(self.arrows())
        return segments


class WaveWV(Wave0):
    ''' Differential Signal, like 2-9 with one state dashed line.

        The solid and dashed lines represent the two signals of a
        differential pair (S+ and its complement S-). At each transition
        the two lines are checked separately: a line rises or falls only
        when its own level actually changes, and stays put otherwise.
    '''
    def _is_top_solid(self) -> bool:
        ''' True if the top line (verts_1) is the solid S+ line. '''
        return self.state in 'wW'

    def _is_top_dashed(self) -> bool:
        ''' True if the top line (verts_1) is the dashed S- line. '''
        return self.state in 'vV'

    def _splus_level(self, level_key: str) -> str:
        ''' Get the S+ (solid) line's level.
            level_key: 'own' (current state), 'prev', or 'next'.
        '''
        if level_key == 'own':
            return _state_level(self.state, prev=False)
        elif level_key == 'prev':
            if _isdiff(self.pstate):
                return _state_level(self.pstate, prev=True)
            return self.plevel
        else: # 'next'
            if _isdiff(self.nstate):
                return _state_level(self.nstate, prev=False)
            return self.nlevel

    def _sminus_level(self, level_key: str) -> str:
        ''' Get the S- (dashed) line's level.
            level_key: 'own' (current state), 'prev', or 'next'.
            For non-diff states, both S+ and S- share the same level.
        '''
        if level_key == 'own':
            return _complement_plevel(_state_level(self.state, prev=False))
        elif level_key == 'prev':
            if _isdiff(self.pstate):
                return _complement_plevel(_state_level(self.pstate, prev=True))
            return self.plevel # non-diff: both lines same as S+
        else: # 'next'
            if _isdiff(self.nstate):
                return _complement_plevel(_state_level(self.nstate, prev=False))
            return self.nlevel # non-diff: both lines same as S+

    def _line_verts(self, is_solid: bool) -> list:
        ''' Build vertices for one line (S+ if is_solid, S- otherwise),
            checking independently whether the line needs to transition
            at the start (entry) and/or end (exit) of this section.
        '''
        if is_solid:
            own_level = self._splus_level('own')
            prev_level = self._splus_level('prev')
            next_level = self._splus_level('next')
        else:
            own_level = self._sminus_level('own')
            prev_level = self._sminus_level('prev')
            next_level = self._sminus_level('next')

        own_y = self.y1 if own_level == '1' else self.y0 if own_level == '0' else self.yhalf
        prev_y = self.y1 if prev_level == '1' else self.y0 if prev_level == '0' else self.yhalf
        next_y = self.y1 if next_level == '1' else self.y0 if next_level == '0' else self.yhalf

        need_entry_rise = (prev_level != own_level and prev_level in '0zV' and own_level == '1')
        need_input_rise = (prev_level != own_level and prev_level in 'V' and own_level == '1')
        need_entry_fall = (prev_level != own_level and prev_level in '1zV' and own_level == '0')
        need_exit_rise = (own_level != next_level and own_level == '0' and next_level in '1V')
        need_exit_fall = (own_level != next_level and own_level == '1' and next_level in '0V')
        next_is_z = (next_level == 'z')

        verts = []

        # --- Entry (start of section) ---
        if prev_level == '-':
            verts.append((self.x0, own_y))
        elif prev_level == own_level and prev_level != 'V':
            verts.append((self.x0, own_y))
        elif need_entry_rise:
            if prev_level == 'z':
                verts.append((self.x0, self.yhalf))
            else:
                verts.append((self.x0, prev_y))
            verts.append((self.x0 + self.rise, own_y))
        elif prev_level == 'V' and own_level != 'V':
            verts.append((self.x0 + self.rise, own_y))
        elif need_entry_fall:
            if prev_level == 'z':
                verts.append((self.x0, self.yhalf))
            else:
                verts.append((self.x0, prev_y))
            verts.append((self.x0 + self.rise, own_y))
        elif need_input_rise:
            verts.append((self.x0 + self.rise, own_y))
        else:
            verts.append((self.x0 + self.rise, own_y))

        # --- Body (stay at own level for the duration)
        if self.xend > self.x0 + self.rise:
            verts.append((self.xend, own_y))

        # --- Exit (end of section)
        if self.nstate in 'qiIQ':
            verts.append((self.xend, own_y))
        elif need_exit_rise:
            if next_is_z:
                verts.append((self.xend + self.rise / 2, self.yhalf))
            else:
                verts.append((self.xend + self.rise, next_y))
        elif need_exit_fall:
            if next_is_z:
                verts.append((self.xend + self.rise / 2, self.yhalf))
            else:
                verts.append((self.xend + self.rise, next_y))
        elif next_level == '-' or next_level == own_level or next_level == 'V':
            verts.append((self.xend, own_y))
        elif next_level == 'z':
            verts.append((self.xend + self.rise / 2, self.yhalf))
        else:
            verts.append((self.xend, own_y))

        # --- Clean up empty verts (single-point path)
        if len(verts) < 2:
            verts.append((verts[0][0] + 0.01, verts[0][1]))

        return verts

    def verts_1(self):
        ''' Verts for the line that is on top in this state.
            For S+-on-top (w/W): top = S+ (solid).
            For S+-on-bottom (v/V): top = S- (dashed).
        '''
        return self._line_verts(is_solid=self._is_top_solid())

    def verts_2(self):
        ''' Verts for the line that is on bottom in this state.
            For S+-on-top (w/W): bottom = S- (dashed).
            For S+-on-bottom (v/V): bottom = S+ (solid).
        '''
        return self._line_verts(is_solid=not self._is_top_solid())

    def segments(self) -> list[SegmentType]:
        verts1 = self.verts_1()
        verts0 = self.verts_2()

        segments: list[SegmentType] = []
        dashed_kwargs = self.kwargs.copy()
        dashed_kwargs['ls'] = ':'
        dashed_kwargs['color'] = 'gray'

        if self.state in 'vV':
            segments.append(Segment(verts1, **dashed_kwargs))
            segments.append(Segment(verts0, **self.kwargs))
        else:
            segments.append(Segment(verts1, **self.kwargs))
            segments.append(Segment(verts0, **dashed_kwargs))

        if self.params.get('data', None):
            segments.append(
                SegmentText((self.xcenter, self.yhalf), self.params['data'][0],
                            color=self.params['datacolor'],
                            fontsize=self.params['datasize'], align=('center', 'center')))
            self.params['data'].pop(0)
        return segments

class WaveWVa(WaveWV):
    ''' Differential Signal (like w/v) with an arrow at the differential
        crossing where the solid line transitions from low to high.

        The arrowhead's centroid is at the crossing point of the two
        signals, and its direction matches the slope of the rise so it
        stays on the line segment for any configured rise time.
    '''
    def arrow(self) -> Segment | None:
        ''' Get arrow at the crossing of the differential signals, where
            the solid line goes from low to high. Returns None if there
            is no low-to-high transition in this section.
        '''
        if self.state in 'W' and self.plevel in '0V':
            # Solid (S+) rises at the start of the section
            xcross = self.x0 + self.rise/2
        elif self.state in 'V' and self.nstate in '1wcC':
            # Solid (S+) rises at the end of the section.
            # nstate 'W' draws its own arrow at the same crossing.
            xcross = self.xend + self.rise/2
        else:
            return None
        return diffarrow(xcross, self.rise, self.y0, self.y1, self.kwargs)

    def segments(self) -> list[SegmentType]:
        ''' Get segments for this wave section '''
        segments = super().segments()
        arrow = self.arrow()
        if arrow is not None:
            segments.append(arrow)
        return segments


class WaveE(Wave0):
    ''' Empty wave section '''
    def verts_in(self) -> list[tuple[float, float]]:
        ''' Get vertices for input transition '''
        return []

    def verts_out(self) -> list[tuple[float, float]]:
        ''' Get vertices for output transition '''
        return []
