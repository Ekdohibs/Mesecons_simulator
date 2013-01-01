Mesecons Simulator
==================

A planning and simulation environment for [Mesecons](http://mesecons.tk/) circuits.

Usage
-----

This program is written in Python. It works with version 2 or 3.

If you have Python 2, you must have the `Tkinter` and `pickle` modules available. Run the `mesecons_simulator.py` file with Python to start the program.

If you have Python 3, you must have the `tkinter` and `pickle` modules available. Run the `mesecons_simulator3.py` file with Python to start the program.

Controls
--------

Key bindings:

  Key      | Purpose
  -------- | -------------------------------------------
  Z        | Viewing level up
  S        | Viewing level down
  R        | Toggle viewing plane between XZ, XY, and YZ
  Ctrl + O | Open a saved simulation file
  Ctrl + S | Save the current simulation to a file

Toolbar buttons (left to right):

  * First button (square with plus sign) extends the cell grid in a given direction.
  * Second button (long addition of two numbers) displays material usage statistics.
  * Third button (mouse cursor) toggles switches, program microcontrollers, or otherwise actuate cells.
  * Fourth button (circular arrow) rotate cells that are directional.

The remaining buttons select the type of object that will be added when a cell on the grid is clicked.

For example, if the blank cell (fifth button) is selected, clicking a cell will clear it.