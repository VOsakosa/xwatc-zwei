"""Das User-Interface für das Spiel, sowie die Hauptklasse."""
import sys
from typing import Self
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton
from attrs import define, field

from xwatc_zwei import LEVELS, loader, verteiler
from xwatc_zwei import geschichte
from xwatc_zwei.geschichte import Entscheidung, Text


@define
class Hauptfenster:
    window: QWidget
    label: QLabel
    buttons_box: QWidget
    buttons: list[QPushButton] = field(factory=list)

    @classmethod
    def create(cls) -> Self:
        window = QWidget()
        window.setWindowTitle("Xwatc II")
        window.setFixedSize(600, 800)

        # Layout und Label hinzufügen
        layout = QVBoxLayout()
        label = QLabel("")
        label.setWordWrap(True)
        layout2 = QVBoxLayout()
        buttons_box = QWidget()
        buttons_box.setLayout(layout2)

        layout.addWidget(label)
        layout.addWidget(buttons_box)

        window.setLayout(layout)
        return cls(window, label, buttons_box)

    def set_text(self, texts: list[str]) -> None:
        self.label.setText("\n".join(texts))
    
    def set_buttons(self, buttons: list[str]) -> None:
        for button in self.buttons:
            button.setParent(None)  # type: ignore
        self.buttons.clear()
        for text in buttons:
            button = QPushButton(text)
            self.buttons.append(button)
            self.buttons_box.layout().addWidget(button)

    def show(self) -> None:
        self.window.show()


@define
class Controller:
    fenster: Hauptfenster
    model: verteiler.Spielzustand | None = None

    def __attrs_post_init__(self):
        # self.view.button.clicked.connect(self.change_text)
        self.next()

    def next(self, wahl_id: str | None = None):
        assert self.model
        texts = []
        while True:
            if wahl_id:
                a = self.model.entscheide(wahl_id)
                wahl_id = None
            else:
                a = self.model.next()
            if isinstance(a, Entscheidung):
                break
            elif isinstance(a, Text):
                texts.append(a.text)
            elif isinstance(a, geschichte.Sprung):
                pass
            else:
                print("Unbekannter Zeilen-Typ!")
        self.fenster.set_text(texts)
        self.fenster.set_buttons([w.text for w in a.wahlen])
        for button, wahl in zip(self.fenster.buttons, a.wahlen):
            button.clicked.connect(lambda *,id=wahl.id:self.next(id))
    


# Hauptfunktion zum Ausführen der Anwendung


def main():
    # Qt-Anwendung initialisieren
    app = QApplication(sys.argv)

    # Model, View und Controller erstellen
    zustand = verteiler.Spielzustand.from_verteiler(loader.load_scenario(LEVELS/"Die_Pilzfee.cfg"))
    view = Hauptfenster.create()
    controller = Controller(view, zustand)

    # Fenster anzeigen
    view.show()

    # Qt-Event-Loop starten
    sys.exit(app.exec_())


# Script starten
if __name__ == '__main__':
    main()
