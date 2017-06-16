from PyQt4.QtGui import *
from PyQt4.QtCore import Qt
from Verb import Verb

class VerbWindow(QWidget):
    def __init__(self):
        super(VerbWindow, self).__init__()

        # Verb Search
        verb_box = QHBoxLayout()
        verb_label = QLabel("Verb: ")
        self.verb_text = QLineEdit("",self)

        verb_box.addWidget(verb_label)
        verb_box.addWidget(self.verb_text)
        search_button = QPushButton("Search", self)
        search_button.clicked.connect(self.__on_search)
        verb_box.addWidget(search_button)

        # Deck selection
        self.deck = QComboBox(self)
        for deck_name in ("Sample Deck 1", "Sample Deck 2"):
            self.deck.addItem(deck_name)
        self.deck.setCurrentIndex(0)

        # Form selection
        personal_forms_box = QVBoxLayout()
        impersonal_forms_box = QVBoxLayout()

        self.checkboxes = {}
        for form in Verb.get_forms():
            checkbox = QCheckBox(form, self)
            checkbox.setChecked(True)
            self.checkboxes[form] = checkbox
            if Verb.is_personal_form(form):
                personal_forms_box.addWidget(checkbox)
            else:
                impersonal_forms_box.addWidget(checkbox)

        forms_box = QHBoxLayout()
        forms_box.addLayout(impersonal_forms_box)
        forms_box.addLayout(personal_forms_box)

        # Table of search results
        self.results_table = QTableWidget(4, 3, self)
        self.results_table.setHorizontalHeaderLabels(["Group", "Conjugation"])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.horizontalHeader().setSortIndicatorShown(False)
        self.results_table.horizontalHeader().setClickable(False)
        self.results_table.horizontalHeader().setResizeMode(QHeaderView.Interactive)
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setMinimumSectionSize(100)
        self.results_table.verticalHeader().setResizeMode(QHeaderView.Fixed)
        self.results_table.setMinimumHeight(275)
        self.results_table.setVisible(False)

        top_box = QVBoxLayout()
        top_box.addLayout(verb_box)
        top_box.addWidget(self.deck)
        top_box.addLayout(forms_box)
        top_box.addWidget(self.results_table)

        self.setLayout(top_box)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setWindowTitle("Add Verb")
        self.show()

    def __on_search(self):
        verb = Verb(unicode(self.verb_text.text()))
        self.results_table.setRowCount(0)
        for row, conjugation in enumerate(verb.conjugations):
            self.results_table.insertRow(row)
            self.results_table.setItem(row, 0, QTableWidgetItem(u"Group {}".format(verb.group)))
            self.results_table.setItem(row, 1, QTableWidgetItem(u"Conjugation {}".format(conjugation)))
            add_button_widget = QWidget()
            add_button = QPushButton("Add")
            add_button.clicked.connect(lambda: self.__on_add(verb, conjugation))
            add_button_layout = QHBoxLayout(add_button_widget)
            add_button_layout.addWidget(add_button)
            add_button_layout.setAlignment(Qt.AlignCenter)
            add_button_layout.setContentsMargins(0, 0, 0, 0)
            add_button_widget.setLayout(add_button_layout)
            self.results_table.setCellWidget(row, 2, add_button_widget)
        self.results_table.setVisible(True)

    def __on_add(self, verb, conjugation):
       pass 


