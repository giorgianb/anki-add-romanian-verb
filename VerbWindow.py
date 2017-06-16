from PyQt4.QtGui import *
from PyQt4.QtCore import Qt
from time import sleep
from Verb import Verb

class VerbWindow(QWidget):
    __model_name = u"Romanian Verb Conjugation"
    def __init__(self, main_window, collection):
        super(VerbWindow, self).__init__()

        self.__locked = False
        self.__collection = collection
        self.__main_window = main_window
        self.__init_gui()

    def __init_gui(self):
        # Verb Search
        verb_box = QHBoxLayout()
        verb_label = QLabel("Verb: ")
        self.__verb_text = QLineEdit("",self)

        verb_box.addWidget(verb_label)
        verb_box.addWidget(self.__verb_text)
        search_button = QPushButton("Search", self)
        search_button.clicked.connect(self.__on_search)
        verb_box.addWidget(search_button)

        # Deck selection
        self.__deck_select = QComboBox(self)
        for deck_name in self.__collection.decks.allNames():
            self.__deck_select.addItem(deck_name, self.__collection.decks.id(deck_name))
        self.__deck_select.setCurrentIndex(0)

        # Form selection
        personal_forms_box = QVBoxLayout()
        impersonal_forms_box = QVBoxLayout()

        self.__forms = {}
        for form in Verb.get_forms():
            if form == "Infinitive":
                continue

            checkbox = QCheckBox(form, self)
            checkbox.setChecked(True)
            self.__forms[form] = checkbox
            if Verb.is_personal_form(form):
                personal_forms_box.addWidget(checkbox)
            else:
                impersonal_forms_box.addWidget(checkbox)

        forms_box = QHBoxLayout()
        forms_box.addLayout(impersonal_forms_box)
        forms_box.addLayout(personal_forms_box)

        # Table of search results
        self.__results_table = QTableWidget(4, 4, self)
        self.__results_table.setHorizontalHeaderLabels(["Infinitive", "Group", "Conjugation", "Add"])
        self.__results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.__results_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.__results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.__results_table.horizontalHeader().setSortIndicatorShown(False)
        self.__results_table.horizontalHeader().setClickable(False)
        self.__results_table.horizontalHeader().setResizeMode(QHeaderView.Interactive)
        self.__results_table.horizontalHeader().setStretchLastSection(True)
        self.__results_table.horizontalHeader().setMinimumSectionSize(100)
        self.__results_table.verticalHeader().setResizeMode(QHeaderView.Fixed)
        self.__results_table.verticalHeader().hide()
        self.__results_table.setMinimumHeight(275)
        self.__results_table.setVisible(False)

        top_box = QVBoxLayout()
        top_box.addLayout(verb_box)
        top_box.addWidget(self.__deck_select)
        top_box.addLayout(forms_box)
        top_box.addWidget(self.__results_table)

        self.setLayout(top_box)
        self.setMinimumWidth(450)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setWindowTitle("Add Verb")
        self.show()

    def __on_search(self):
        verb = Verb(unicode(self.__verb_text.text()))
        self.__results_table.setRowCount(0)
        for row, specifier in enumerate(verb.specifiers):
            self.__results_table.insertRow(row)
            self.__results_table.setItem(
                    row, 
                    0, 
                    QTableWidgetItem(specifier.infinitive)
                    )
            self.__results_table.setItem(row, 1, QTableWidgetItem(specifier.group))
            self.__results_table.setItem(row, 2, QTableWidgetItem(specifier.conjugation))
            add_button_widget = QWidget()
            add_button = QPushButton("Add")
            add_button.clicked.connect(lambda: self.__on_add(verb, specifier))
            add_button_layout = QHBoxLayout(add_button_widget)
            add_button_layout.addWidget(add_button)
            add_button_layout.setAlignment(Qt.AlignCenter)
            add_button_layout.setContentsMargins(0, 0, 0, 0)
            add_button_widget.setLayout(add_button_layout)
            self.__results_table.setCellWidget(row, 3, add_button_widget)
        self.__results_table.setVisible(True)

    def __get_custom_model(self):
        manager = self.__collection.models
        model = manager.byName(self.__model_name)
        if not model:
            model = manager.new(self.__model_name)
            field = manager.newField("Form")
            manager.addField(model, field)
            field = manager.newField("Subject")
            manager.addField(model, field)
            field = manager.newField("Infinitive")
            manager.addField(model, field)
            field = manager.newField("Conjugation")
            manager.addField(model, field)
            template = manager.newTemplate("Card 1")
            template['qfmt'] = "{{Form}}\n\n\n\n[{{Subject}}] {{Infinitive}}"
            template['afmt'] = "{{FrontSide}}\n\n<hr id=answer>\n\n{{Conjugation}}"
            manager.addTemplate(model, template)
            manager.add(model)

        return model


    def __on_add(self, verb, specifier):
        while self.__locked:
            sleep(1)

        self.__locked = True
        self.__verb_text.setReadOnly(True)
        self.__deck_select.setEditable(False)

        deck_id = self.__deck_select.itemData(self.__deck_select.currentIndex())
        self.__collection.decks.select(deck_id)
        model = self.__get_custom_model()
        model['did'] = deck_id
        self.__collection.models.save(model)
        self.__collection.models.setCurrent(model)

        verb_infinitive = verb.conjugate("Infinitive", specifier)[None]
        for form, checkbox in self.__forms.iteritems():
            if not checkbox.isChecked():
                continue

            conjugations = verb.conjugate(form, specifier)
            for subject, conjugation in conjugations.iteritems():
                subject = "Impersonal" if subject is None else subject
                card = self.__collection.newNote()
                card[u"Form"] = form
                card[u"Subject"] = subject
                card[u"Infinitive"] = verb_infinitive
                card[u"Conjugation"] = conjugation
                card.tags.append(form.replace(" ", "_"))
                card.tags.append(subject.replace(" ", "_"))

                self.__collection.addNote(card)
                self.__collection.save()

        self.__collection.reset()
        self.__main_window.reset()
        self.__deck_select.setEditable(True)
        self.__verb_text.setReadOnly(False)
        self.__locked = False
