# -*- coding: utf-8 -*-
from aqt import mw
from aqt.qt import *

#PyQT
from PyQt4.QtGui import *
from bs4 import BeautifulSoup
import urllib


class VerbWindow(QWidget):
    conjugations = [
            "Long Infinitive",
            "Participle",
            "Gerund",
            "Imperative",
            "Present Indicative",
            "Present Subjunctive",
            "Imperfect Indicative",
            "Simple Perfect Indicative",
            "More Than Perfect Indicative"
        ]
    def __init__(self):
        super(VerbWindow, self).__init__()

        self.__model_name = u"Romanian Verb Conjugation"
        self.__initGUI()

    def __initGUI(self):
        self.verb_box = QHBoxLayout()
        self.verb_label = QLabel("Verb: ")
        self.verb_text = QLineEdit("",self)

        self.verb_box.addWidget(self.verb_label)
        self.verb_box.addWidget(self.verb_text)
        self.add_button = QPushButton("Add", self)
        self.add_button.clicked.connect(self.__on_add)
        self.verb_box.addWidget(self.add_button)

        self.deck = QComboBox(self)
        for deck_name in mw.col.decks.allNames():
            self.deck.addItem(deck_name, mw.col.decks.id(deck_name))
        self.deck.setCurrentIndex(0)

        self.conjugations_box = QVBoxLayout()

        self.checkboxes = {}
        for conjugation in VerbWindow.conjugations:
            checkbox = QCheckBox(conjugation, self)
            checkbox.setChecked(True)
            self.checkboxes[conjugation] = checkbox
            self.conjugations_box.addWidget(checkbox)

        self.top_box = QVBoxLayout()
        self.top_box.addLayout(self.verb_box)
        self.top_box.addWidget(self.deck)
        self.top_box.addLayout(self.conjugations_box)

        self.setLayout(self.top_box)
        self.setMinimumWidth(200)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setWindowTitle("Add Verb")
        self.show()

    def __get_custom_model(self):
        manager = mw.col.models
        model = manager.byName(self.__model_name)
        if not model:
            model = manager.new(self.__model_name)
            front = manager.newField("Front")
            manager.addField(model, front)
            back = manager.newField("Back")
            manager.addField(model, back)
            template = manager.newTemplate("Card 1")
            template['qfmt'] = "{{Front}}"
            template['afmt'] = "{{FrontSide}}\n\n<hr id=answer>\n\n{{Back}}"
            manager.addTemplate(model, template)
            manager.add(model)

        return model



    def __on_add(self):
        self.verb_text.setReadOnly(True)
        self.deck.setEditable(False)
        """
        for checkbox in self.checkboxes.values():
            checkbox.setCheckable(False)
            """

        url = "https://dexonline.ro/definitie/" + urllib.quote(self.verb_text.text().encode('utf-8'))
        soup = BeautifulSoup(urllib.urlopen(url), "html.parser")

        deck = mw.col
        deck_id = self.deck.itemData(self.deck.currentIndex())
        deck.decks.select(deck_id)
        model = self.__get_custom_model()
        model['did'] = deck_id
        deck.models.save(model)
        deck.models.setCurrent(model)

        personal_conjugations = {
                'Present Indicative' : get_present_indicative,
                'Present Subjunctive' : get_present_subjunctive,
                'Imperfect Indicative' : get_imperfect_indicative,
                'Simple Perfect Indicative' : get_simple_perfect_indicative,
                'More Than Perfect Indicative' : get_more_than_perfect_indicative
                }

        subject_pronouns = ["Eu", "Tu", "El/Ea", "Noi", "Voi", "Ei/Ele"]
        subjects = [
                "First Person Singular",
                "Second Person Singular",
                "Third Person Singular",
                "First Person Plural",
                "Second Person Plural",
                "Third Person Plural",
        ]


        tables = soup.select("table")
        for table in tables:
            if "verb" in table.text:
                bad_forms = table.select('.notRecommended')
                for form in bad_forms:
                    form.clear()
                rows = table.select("tr")
                break

        infinitive = get_infinitive(rows)
        for tag, f in personal_conjugations.items():
            if not self.checkboxes[tag].isChecked():
                continue
            conjugations = f(rows)
            for subject, subject_pronoun, conjugation in zip(subjects, subject_pronouns, conjugations):
                card = deck.newNote()
                card[u'Front'] = u'{} <br><br>[{}] {}'.format(tag, subject_pronoun, infinitive)
                card[u'Back'] = conjugation
                card.tags.append(tag.replace(" ", "_"))
                card.tags.append(subject.replace(" ", "_"))

                deck.addNote(card)
                deck.save()

        impersonal_conjugations = {
            "Long Infinitive" : get_long_infinitive,
            "Participle" : get_participle,
            "Gerund" : get_gerund
        }
        for tag, f in impersonal_conjugations.items():
            if not self.checkboxes[tag].isChecked():
                continue
            conjugation = f(rows)
            card = deck.newNote()
            card[u'Front'] = u'[{}] {}'.format(tag, infinitive)
            card[u'Back'] = conjugation
            card.tags.append(tag.replace(" ", "_"))
            card.tags.append(subject.replace(" ", "_"))

            deck.addNote(card)
            deck.save()

        if self.checkboxes["Imperative"].isChecked():
            conjugations = get_imperative(rows)
            card = deck.newNote()
            card[u'Front'] = u'[{}] {}'.format("Second Person Singular Imperative", infinitive)
            card[u'Back'] = conjugations[0]
            card.tags.append("Imperative")
            card.tags.append("Second_Person_Singular")
            deck.addNote(card)
            deck.save()
            card = deck.newNote()
            card[u'Front'] = u'[{}] {}'.format("Second Person Plural Imperative", infinitive)
            card[u'Back'] = conjugations[1]
            card.tags.append("Imperative")
            card.tags.append("Second_Person_Plural")
            deck.addNote(card)
            deck.save()


        mw.col.reset()
        mw.reset()

        for checkbox in self.checkboxes.values():
            checkbox.setCheckable(True)
        self.deck.setEditable(False)
        self.verb_text.setReadOnly(False)
        self.verb_text.setText("")


def run_add_verb_plugin():
    global __window
    __window = VerbWindow();




# create a new menu item, "test"
action = QAction("Add Romanian Verb", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(run_add_verb_plugin)
# and add it to the tools menu
mw.form.menuTools.addAction(action)

def add_accent(td):
    spans = td.select(".accented")
    for span in spans:
        span.string = u"<u>" + span.text + u"</u>"

    return td

def get_present_indicative(rows):
    ROW_BEGIN = 5
    SUBJECT_COUNT = 6

    conjugations = []

    for i in range(ROW_BEGIN, ROW_BEGIN + SUBJECT_COUNT):
        if i == ROW_BEGIN or i == ROW_BEGIN + SUBJECT_COUNT / 2:
            c = rows[i].td.find_next_siblings()[1]
            add_accent(c)
            c = c.text.strip()
        else:
            c = rows[i].td.find_next_sibling()
            add_accent(c)
            c = c.text.strip()

        conjugations.append(c)

    return conjugations

def get_present_subjunctive(rows):
    ROW_BEGIN = 5
    SUBJECT_COUNT = 6

    conjugations = []

    for i in range(ROW_BEGIN, ROW_BEGIN + SUBJECT_COUNT):
        if i == ROW_BEGIN or i == ROW_BEGIN + SUBJECT_COUNT / 2:
            c = rows[i].td.find_next_siblings()[2]
            add_accent(c)
            c = c.text.strip()
        else:
            c = rows[i].td.find_next_siblings()[1]
            add_accent(c)
            c = c.text.strip()

        c = c.split('\n')
        c = ' '.join(word.strip() for word in c)

        conjugations.append(c)

    return conjugations

def get_imperfect_indicative(rows):
    ROW_BEGIN = 5
    SUBJECT_COUNT = 6

    conjugations = []

    for i in range(ROW_BEGIN, ROW_BEGIN + SUBJECT_COUNT):
        if i == ROW_BEGIN or i == ROW_BEGIN + SUBJECT_COUNT / 2:
            c = rows[i].td.find_next_siblings()[3]
            add_accent(c)
            c = c.text.strip()
        else:
            c = rows[i].td.find_next_siblings()[2]
            add_accent(c)
            c = c.text.strip()

        conjugations.append(c)

    return conjugations

def get_simple_perfect_indicative(rows):
    ROW_BEGIN = 5
    SUBJECT_COUNT = 6
    conjugations = []

    for i in range(ROW_BEGIN, ROW_BEGIN + SUBJECT_COUNT):
        if i == ROW_BEGIN or i == ROW_BEGIN + SUBJECT_COUNT / 2:
            c = rows[i].td.find_next_siblings()[4]
            add_accent(c)
            c = c.text.strip()
        else:
            c = rows[i].td.find_next_siblings()[3]
            add_accent(c)
            c = c.text.strip()

        conjugations.append(c)

    return conjugations

def get_more_than_perfect_indicative(rows):
    ROW_BEGIN = 5
    SUBJECT_COUNT = 6

    conjugations = []

    for i in range(ROW_BEGIN, ROW_BEGIN + SUBJECT_COUNT):
        if i == ROW_BEGIN or i == ROW_BEGIN + SUBJECT_COUNT / 2:
            c = rows[i].td.find_next_siblings()[5]
            add_accent(c)
            c = c.text.strip()
        else:
            c = rows[i].td.find_next_siblings()[4]
            add_accent(c)
            c = c.text.strip()

        conjugations.append(c)

    return conjugations

def get_infinitive(rows):
    c = add_accent(rows[1].td)
    c = c.text.strip()
    c = c.split('\n')
    c = ' '.join(word.strip() for word in c)
    return c

def get_long_infinitive(rows):
    c = rows[1].td.find_next_sibling()
    add_accent(c)
    c = c.text.strip()
    return c


def get_participle(rows):
    c = rows[1].td.find_next_siblings()[1]
    add_accent(c)
    c = c.text.strip()
    return c

def get_gerund(rows):
    c =  rows[1].td.find_next_siblings()[2]
    add_accent(c)
    c = c.text.strip()
    return c

def get_imperative(rows):
    conjugations = []
    c = rows[2].td
    add_accent(c)
    c = c.text.strip()
    conjugations.append(c)
    c = rows[2].td.find_next_sibling()
    add_accent(c)
    c = c.text.strip()
    conjugations.append(c)
    return conjugations

