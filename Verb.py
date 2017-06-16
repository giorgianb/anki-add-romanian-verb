# -*- coding: utf-8 *-*
from bs4 import BeautifulSoup
from collections import namedtuple
import urllib

class InvalidConjugationError(Exception):
    pass

ConjugationSpecifier = namedtuple("ConjugationSpecifier", "infinitive group conjugation")

class Verb(object):
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
        soup = BeautifulSoup(urllib.urlopen(url), "html.parser")

        tables = soup.select("table")
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
            infinitives.append(candidate.parent.select(".lexemName")[0].text.strip())

        return tuple(infinitives)
        
    @staticmethod
    def __get_groups(candidates):
        groups = []
        for candidate in candidates:
            labels = candidate.parent.select("label")
            label = [label.text for label in labels if "grupa" in label.text][0]
            groups.append(label[len("grupa a "):label.find("-a")])

        return tuple(groups)

    @staticmethod
    def __get_conjugations(candidates):
        conjugations = []
        for candidate in candidates:
            labels = candidate.parent.select("label")
            label = [label.text for label in labels if "conjugarea" in label.text][0]
            conjugations.append(label[len("conjugarea a "):label.find("-a")])

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
            raise InvalidConjugationError("{} is not a valid conjugation.".format(conjugation))

        conjugations = {}
        table = self.__candidates[specifier]
        for subject, location in self.__forms[form].iteritems():
            form = self.__table_lookup(table, location)
            if form != u"—":
                conjugations[subject] = form

        return conjugations

    @staticmethod
    def __table_lookup(table, location):
        row = table.select("tr")[location[0]]
        if location[1] == 0:
             entry = row.td
        else:
            entry = row.td.find_next_siblings()[location[1] - 1]

        bad_forms = entry.select(".notRecommended")
        for form in bad_forms:
            form.clear()

        spans = entry.select(".accented")
        for span in spans:
            span.string = u"<u>" + span.text + u"</u>"

        words = [word.strip() for word in entry.text.strip().split('\n')]
        return ' '.join(words)
