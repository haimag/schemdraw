.. _gallerytiming:

Timing Diagrams
---------------

.. jupyter-execute::
    :hide-code:

    import schemdraw
    from schemdraw import elements as elm
    from schemdraw import logic
    schemdraw.use('svg')


Timing diagrams, based on `WaveDrom <https://wavedrom.com/>`_, are drawn using the :py:class:`schemdraw.logic.timing.TimingDiagram` class.

.. code-block:: python

    from schemdraw import logic



SRAM read/write cycle
^^^^^^^^^^^^^^^^^^^^^

The SRAM examples make use of Schemdraw's extended 'edge' notation for labeling
timings just above and below the wave.

.. jupyter-execute::
    :code-below:
    
    logic.TimingDiagram(
        {'signal': [
            {'name': 'Address',     'wave': 'x4......x.', 'data': ['Valid address']},
            {'name': 'Chip Select', 'wave': '1.0.....1.'},
            {'name': 'Out Enable',  'wave': '1.0.....1.'},
            {'name': 'Data Out',    'wave': 'z...x6...z', 'data': ['Valid data']},
        ],
         'edge': ['[0.4:1.2]+[0.4:8] $t_{WC}$',
                  '[0.9:1]+[0.9:5] $t_{AQ}$',
                  '[1:2]+[1:5] $t_{EQ}$',
                  '[2:2]+[2:5] $t_{GQ}$',
                  '[0.4:5]-[3.9:5]{lightgray,:}',
                 ]
        }, ygap=.5, grid=False)


.. jupyter-execute::
    :code-below:
    
    logic.TimingDiagram(
        {'signal': [
            {'name': 'Address',      'wave': 'x4......x.', 'data': ['Valid address']},
            {'name': 'Chip Select',  'wave': '1.0......1'},
            {'name': 'Write Enable', 'wave': '1..0...1..'},
            {'name': 'Data In',      'wave': 'x...5....x', 'data': ['Valid data']},
        ],
         'edge': ['[0.4:1]+[0.4:8] $t_{WC}$',
                  '[2:1]+[2:3] $t_{SA}$',
                  '[3.4:4]+[3.4:7] $t_{WD}$',
                  '[3.4:7]+[3.4:9] $t_{HD}$',
                  '[0.4:1]-[2:1]{lightgray,:}'],
        }, ygap=.4, grid=False)



J-K Flip Flop
^^^^^^^^^^^^^

Timing diagram for a J-K flip flop taken from `here <https://commons.wikimedia.org/wiki/File:JK_timing_diagram.svg>`_.
Notice the use of the `async` dictionary parameter on the J and K signals, and the color parameters for the output signals.

.. jupyter-execute::
    :code-below:

    logic.TimingDiagram(
        {'signal': [
            {'name': 'clk', 'wave': 'P......'},
            {'name': 'J', 'wave': '0101', 'async': [0, .8, 1.3, 3.7, 7]},
            {'name': 'K', 'wave': '010101', 'async': [0, 1.2, 2.3, 2.8, 3.2, 3.7, 7]},
            {'name': 'Q', 'wave': '010.101', 'color': 'red', 'lw': 1.5},
            {'name': r'$\overline{Q}$', 'wave': '101.010', 'color': 'blue', 'lw': 1.5}],
        'config': {'hscale': 1.5}}, risetime=.05)

SDRAM Timing Diagram
^^^^^^^^^^^^^^^^^^^^

.. jupyter-execute::
    :code-below:

    logic.TimingDiagram.from_json('''
    {"signal": [
        {"name": "DTI_CLOCK", "wave": "01010101010101010101010101010101010101010101"},
        {"name": "DTI_CMD[0]", "wave": "x2.........2.2.............................x", "data": ["DES", "RD", "DES"]},
        {"name": "DTI_CMD[1]",       "wave": "x2.2.2....|................................x", "data": ["DES", "RD", "DES"]},
        {"name": "DTI_RDDATA_EN[0]", "wave": "0.........|....1...0...1...0................", "data": ["DES", "RD", "DES"]},
        {"name": "DTI_RDDATA_EN[1]", "wave": "0.........|....1...0.1...0..................", "data": ["DES", "RD", "DES"]},
        {"name": "DTI_RDDATA[0]",       "wave": "x2........|..................2.2.2...2.2.2.x", "data": ["", "D0", "D0", "", "D1", "D1"]},
        {"name": "DTI_RDDATA[1]",       "wave": "x2........|..................2.2.2.2.2.2...x", "data": ["", "D0", "D0", "", "D1", "D1"]},
        {"name": "DTI_RDDATA_VALID[0]", "wave": "0.........|..................1...0...1...0.."},
        {"name": "DTI_RDDATA_VALID[1]", "wave": "0............................1...0.1...0...."},
        {"name": "PHASE", "data": "{1 0}" },
        {},
        {"name": "PHY_PHY_CLOCK", "wave": "p..........................................."},
        {"name": "PHY_CMD",       "wave": "x2......22.....22..........................x", "data": ["DES", "RD", "DES", "RD", "DES"]},
        {"name": "PHY_RDDATA_EN", "wave": "0..............|..1...0..1...0.............."},
        {"name": "PHY_RDDATA",       "wave": "x2.............|..........22222...22222....x", "data": ["", "D0", "D0", "D0", "D0", "", "D1", "D1", "D1", "D1", ""]},
        {"name": "PHY_RDDATA_VALID", "wave": "0..............|..........1...0...1...0.....", "data": ["", "D0", "D0", "D0", "D0", "", "D1", "D1", "D1", "D1", ""]},
        {},
        {"name": "MEM_CK",    "wave": "Q..........................................."},
        {"name": "MEM_CMD",   "wave": "x2.........22.....22.......................x", "data": ["DES", "RD", "DES", "RD"]},
        {"name": "MEM_DQ",    "wave": "z..................|...bbbbz...bbbbz........", "data": ["0", "0", "0", "0", "0", "0", "0", "0", "1", "1", "1", "1", "1", "1", "1", "1"], "color": "blue"},
        {"name": "MEM_DQS/N", "wave": "z..................|..Q....z..Q....z........", "color": "blue"},

    ],
    "shade": [
        "odd 0:9 #eee",
    ],
    "edge": [
        "[0.9:5]-[10.9:5]{red}",
        "[2.9:17]-[10.9:17]{red}",
        "[10:5]<->[10:17]{red} tPHY_RDLAT=ROUNDDOWN((RL+CMD_PHASE)/2)",
        "[11.4:5]<->[11.4:9]{red} tCMDGEAR_DELAY",
        "[11.4:9]-[16.9:9]{red}",
        "[11.4:17]<->[11.4:19]{red} tDA",
        "[10:19]-[16.9:19]{red}",
        "[15.9:19]<->[15.9:27]{red} tPHY_RDLAT",
        "[15.4:27]-[16.9:27]{red}",
        "[16:23]<->[16:27]{red} tPHY_RDVLD",
        "[16:23]-[20.9:23]{red}",
        "[20.4:23]<->[20.4:12]{red} RL=19",
        "[20.4:12]-[16.4:12]{red}",
        "[16:12]<->[16:9]{red} tCTRL_DELAY",

        "[3.4:17]->[13:18]{blue}",
        "[4.4:23]->[13:25]{blue}",
        "[3.4:23]-[4.9:23]{red}",

        ],
    "config": {"hscale": .75}
    }''',

    nodealign='clock'
    )


Tutorial Examples
^^^^^^^^^^^^^^^^^

These examples were copied from `WaveDrom Tutorial <https://wavedrom.com/tutorial.html>`_.
They use the `from_json` class method so the examples can be pasted directly as a string. Otherwise, the setup must be converted to a proper Python dictionary.

.. jupyter-execute::
    :code-below:
    
    logic.TimingDiagram.from_json('''{ signal: [{ name: "Alfa", wave: "01.zx=ud.23.456789" }] }''')
    
    
.. jupyter-execute::
    :code-below:
    
    logic.TimingDiagram.from_json('''{ signal: [
      { name: "clk",         wave: "p.....|..." },
      { name: "Data",        wave: "x.345x|=.x", data: ["head", "body", "tail", "data"] },
      { name: "Request",     wave: "0.1..0|1.0" },
      {},
      { name: "Acknowledge", wave: "1.....|01." }
      ]}''')
