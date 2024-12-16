import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QTextEdit, QVBoxLayout, QWidget, QLineEdit, QLabel, \
    QHBoxLayout, QFileDialog
from PyQt6.QtCore import QTimer
from libs.Backend import ControlClient
import time


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Runker")

        self.server_address_input = QLineEdit()
        self.server_address_input.setText("localhost")
        self.server_port_input = QLineEdit()
        self.server_port_input.setText("12345")
        self.connect_button = QPushButton("Connecter")
        self.connect_button.clicked.connect(self.connect_to_server)

        self.code_input = QTextEdit()
        self.code_input.setPlaceholderText("Entrez le code à exécuter ici")

        self.load_button = QPushButton("Charger un fichier")
        self.load_button.clicked.connect(self.load_file)

        self.run_button = QPushButton("Exécuter le code")
        self.run_button.clicked.connect(self.run_code)
        self.run_button.setEnabled(False)

        self.output_display = QTextEdit()
        self.output_display.setReadOnly(True)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel("Adresse:"))
        top_layout.addWidget(self.server_address_input)
        top_layout.addWidget(QLabel("Port:"))
        top_layout.addWidget(self.server_port_input)
        top_layout.addWidget(self.connect_button)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.code_input)
        layout.addWidget(self.load_button)
        layout.addWidget(self.run_button)
        layout.addWidget(self.output_display)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.backend = None

        # Ajouter un QTimer pour mettre à jour régulièrement l'affichage
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_output_display)

    def connect_to_server(self):
        self.connect_button.setEnabled(False)
        if self.backend:
            self.backend.close()
        address = self.server_address_input.text()
        port = int(self.server_port_input.text())

        self.backend = ControlClient(serverAddress=address, serverPort=port, certfile="usercertfile.pem")
        self.backend.requestUid()
        time.sleep(0.1)
        self.output_display.append(f"Connecté au serveur avec UID: {self.backend.uid}")
        self.run_button.setEnabled(True)
        self.timer.start(15)

    def load_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Ouvrir un fichier", "", "Tous les fichiers (*)")
        if file_name:
            with open(file_name, 'r') as file:
                file_content = file.read()
                self.code_input.setPlainText(file_content)

    def run_code(self):
        self.run_button.setEnabled(False)
        code = self.code_input.toPlainText()
        print("Running code:", code)
        self.backend.runCode(code)

    def update_output_display(self):
        if self.backend:
            while self.backend.printbuffer:
                self.output_display.append(self.backend.printbuffer.pop(0))

            if self.backend.running:
                if not self.run_button.isEnabled():
                    self.run_button.setEnabled(True)
                if self.connect_button.isEnabled():
                    self.connect_button.setEnabled(False)
            else:
                if self.run_button.isEnabled():
                    self.run_button.setEnabled(False)
                if not self.connect_button.isEnabled():
                    self.connect_button.setEnabled(True)

            if self.backend.dataclient_running:
                if self.run_button.isEnabled():
                    self.run_button.setEnabled(False)
            else:
                if not self.run_button.isEnabled():
                    time.sleep(0.5)
                    if not self.backend.dataclient_running:
                        self.run_button.setEnabled(True)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()