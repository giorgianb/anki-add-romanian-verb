from aqt import mw
from VerbWindow import VerbWindow
from PyQt4.QtGui import QAction

def run_add_romanian_verb_plugin():
    global __window
    __window = VerbWindow(mw, mw.col);

action = QAction("Add Romanian Verb", mw)
action.triggered.connect(run_add_romanian_verb_plugin)
mw.form.menuTools.addAction(action)
