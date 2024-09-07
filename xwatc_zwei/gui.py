"""Das User-Interface für das Spiel, sowie die Hauptklasse."""
import sys
from typing import Self
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from attrs import define

from xwatc_zwei.verteiler import Hauptgeschichte


@define
class Hauptfenster:
    window: QWidget
    label: QLabel

    @classmethod
    def create(cls) -> Self:
        window = QWidget()
        window.setWindowTitle("Hallo Welt!")

        # Layout und Label hinzufügen
        layout = QVBoxLayout()
        label = QLabel("Hallo Welt!")

        layout.addWidget(label)
        window.setLayout(layout)
        return cls(window, label)

    def set_text(self, text: str) -> None:
        self.label.setText(text)
    
    def show(self) -> None:
        self.window.show()

@define
class Controller:
    fenster: Hauptfenster
    model: Hauptgeschichte | None = None
    
    
    def __attrs_post_init__(self):
        # self.view.button.clicked.connect(self.change_text)
        pass
    
    def change_text(self):
        # TODO
        pass

# Hauptfunktion zum Ausführen der Anwendung
def main():
    # Qt-Anwendung initialisieren
    app = QApplication(sys.argv)
    
    # Model, View und Controller erstellen
    # model = Model()
    view = Hauptfenster.create()
    controller = Controller(view)
    
    # Fenster anzeigen
    view.show()
    
    # Qt-Event-Loop starten
    sys.exit(app.exec_())

# Script starten
if __name__ == '__main__':
    main()