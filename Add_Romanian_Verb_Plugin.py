# -*- coding: utf-8 *-*
from BeautifulSoup import BeautifulSoup
from collections import namedtuple
import urllib
from aqt import mw
from PyQt4.QtGui import *
from PyQt4.QtCore import Qt
from time import sleep

class InvalidConjugationError(Exception):
    pass

ConjugationSpecifier = namedtuple("ConjugationSpecifier", "infinitive group conjugation")

class RomanianVerb(object):
    __forms = {
            "Infinitive" : {None : (1, 0)},
            "Long Infinitive" : {None : (1, 1)},
            "Participle" : {None : (1, 2)},
            "Gerund" : {None: (1, 3)},
            "Imperative" : {"tu" : (2, 0), "voi" : (2, 1)},
            "Present Indicative" : {
                "eu" : (5, 2),
                "tu" : (6, 1),
                "el/ea" : (7, 1),
                "noi" : (8, 2),
                "voi" : (9, 1),
                "ei/ele" : (10, 1)
                },
            "Present Subjunctive" : {
                "eu" : (5, 3),
                "tu" : (6, 2),
                "el/ea" : (7, 2),
                "noi" : (8, 3),
                "voi" : (9, 2),
                "ei/ele" : (10, 2)
                },
            "Imperfect Indicative" : {
                "eu" : (5, 4),
                "tu" : (6, 3),
                "el/ea" : (7, 3),
                "noi" : (8, 4),
                "voi" : (9, 3),
                "ei/ele" : (10, 3)
                },
            "Simple Perfect Indicative" : {
                "eu" : (5, 5),
                "tu" : (6, 4),
                "el/ea" : (7, 4),
                "noi" : (8, 5),
                "voi" : (9, 4),
                "ei/ele" : (10, 4)
                },
            "More Than Perfect Indicative" : {
                "eu" : (5, 6),
                "tu" : (6, 5),
                "el/ea" : (7, 5),
                "noi" : (8, 6),
                "voi" : (9, 5),
                "ei/ele" : (10, 5)
                }
            }
            

    __url = "https://dexonline.ro/definitie/{verb}"

    def __init__(self, verb):
        url = self.__url.format(verb=urllib.quote(verb.encode("utf8")))
        soup = BeautifulSoup(urllib.urlopen(url))


        tables = soup.findAll("table")
        tables = tuple(table for table in tables if "verb" in table.text)
        infinitives = self.__get_infinitives(tables)
        conjugations = self.__get_conjugations(tables)
        groups = self.__get_groups(tables)

        specifiers = []
        for infinitive, group, conjugation in zip(infinitives, groups, conjugations):
            specifiers.append(ConjugationSpecifier(infinitive, group, conjugation))
        self.__candidates = dict(zip(specifiers, tables))

    @staticmethod
    def __get_infinitives(candidates):
        infinitives = []
        for candidate in candidates:
            infinitives.append(candidate.parent.findAll(attrs="lexemName")[0].text.strip())

        return tuple(infinitives)
        
    @staticmethod
    def __get_groups(candidates):
        groups = []
        for candidate in candidates:
            labels = candidate.parent.findAll("label")
            label = [label.text for label in labels if "grupa" in label.text][0]
            groups.append(label[len("grupa a "):label.find("-a")])

        return tuple(groups)

    @staticmethod
    def __get_conjugations(candidates):
        conjugations = []
        for candidate in candidates:
            labels = candidate.parent.findAll("label")
            labels = [label.text for label in labels if "conjugarea" in label.text]
            if len(labels) > 0:
                label = labels[0]
                conjugations.append(label[len("conjugarea a "):label.find("-a")])
            else:
                conjugations.append("irregular")

        return tuple(conjugations)

    @property
    def specifiers(self):
        return self.__candidates.keys()

    @property
    def forms(self):
        return self.__forms.keys()

    @classmethod
    def get_forms(cls):
        return cls.__forms.keys()

    @classmethod
    def is_personal_form(cls, form):
        if form not in cls.get_forms():
            raise InvalidFormError("{} is not a valid form.".format(form))

        return None not in cls.__forms[form]

    @classmethod
    def is_impersonal_form(cls, form):
        if form not in cls.get_forms():
            raise InvalidFormError("{} is not a valid form.".format(form))

        return None in cls.__forms[form]

    def conjugate(self, form, specifier):
        if form not in self.forms:
            raise InvalidFormError("{} is not a valid form.".format(form))
        elif specifier not in self.specifiers:
            raise InvalidConjugationError("{} is not a valid specifier.".format(specifier))

        conjugations = {}
        table = self.__candidates[specifier]
        for subject, location in self.__forms[form].iteritems():
            form = self.__table_lookup(table, location)
            if form != u"—":
                conjugations[subject] = form

        return conjugations

    @staticmethod
    def __table_lookup(table, location):
        row = table.findAll("tr")[location[0]]
        if location[1] == 0:
             entry = row.td
        else:
            entry = row.td.findNextSiblings()[location[1] - 1]

        bad_forms = entry.findAll(attrs="notRecommended")
        for form in bad_forms:
            form.clear()

        spans = entry.findAll(attrs="accented")
        for span in spans:
            span.string = u"<u>" + span.text + u"</u>"

        words = [word.strip() for word in entry.text.strip().split('\n')]
        return ' '.join(words)


class RomanianVerbWindow(QWidget):
    __model_name = u"Romanian Verb Conjugation"
    def __init__(self, main_window, collection):
        super(RomanianVerbWindow, self).__init__()

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
        for form in RomanianVerb.get_forms():
            if form == "Infinitive":
                continue

            checkbox = QCheckBox(form, self)
            checkbox.setChecked(True)
            self.__forms[form] = checkbox
            if RomanianVerb.is_personal_form(form):
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
        self.setWindowTitle("Add Romanian Verb")
        self.show()

    def __on_search(self):
        verb = RomanianVerb(self.__verb_text.text())
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
            # Lambda is weird to capture specifier's object
            add_button.clicked.connect((lambda spec: lambda: self.__on_add(verb, spec))(specifier))
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
        self.__verb_text.setReadOnly(False)
        self.__locked = False
def run_add_romanian_verb_plugin():
    global __window
    __window = RomanianVerbWindow(mw, mw.col);

action = QAction("Add Romanian Verb", mw)
action.triggered.connect(run_add_romanian_verb_plugin)
mw.form.menuTools.addAction(action)


