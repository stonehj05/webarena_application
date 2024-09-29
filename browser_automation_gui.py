import sys
import re
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, QPushButton
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from browser_env import ScriptBrowserEnv, create_id_based_action, create_stop_action

class BrowserController(QObject):
    update_signal = pyqtSignal(str)

    def __init__(self, config_file):
        super().__init__()
        self.config_file = config_file
        self.env = None
        self.obs = None
        self.info = None

    @pyqtSlot()
    def initialize_browser(self):
        try:
            self.env = ScriptBrowserEnv(
                headless=False,
                slow_mo=100,
                observation_type="accessibility_tree",
                current_viewport_only=True,
                viewport_size={"width": 1280, "height": 720},
            )
            self.obs, self.info = self.env.reset(options={"config_file": self.config_file})
            self.update_signal.emit(f"Browser initialized. Current URL: {self.env.page.url}\n\nObservation:\n{self.obs['text']}")
        except Exception as e:
            self.update_signal.emit(f"Error initializing browser: {str(e)}")

    @pyqtSlot(str)
    def perform_action(self, action_text):
        try:
            if action_text.startswith("click "):
                match = re.search(r"\[(\d+)\]", action_text)
                if match:
                    element_id = match.group(1)
                    action = create_id_based_action(f"click [{element_id}]")
                    
                    # Get the current URL before the action
                    before_url = self.env.page.url
                    
                    self.obs, reward, terminated, truncated, self.info = self.env.step(action)
                    
                    # Get the URL after the action
                    after_url = self.env.page.url
                    
                    # Prepare the feedback message
                    feedback = f"Clicked element [{element_id}]\n"
                    feedback += f"Before URL: {before_url}\n"
                    feedback += f"After URL: {after_url}\n"
                    feedback += f"Reward: {reward}, Terminated: {terminated}, Truncated: {truncated}\n\n"
                    feedback += f"New Observation:\n{self.obs['text']}"
                    
                    self.update_signal.emit(feedback)
                else:
                    self.update_signal.emit("Invalid click command. Use format: click [ID]")
            else:
                self.update_signal.emit(f"Unknown command: {action_text}")
        except Exception as e:
            self.update_signal.emit(f"Error performing action: {str(e)}")

class BrowserAutomationGUI(QWidget):
    action_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.initUI()
        
        self.browser_controller = BrowserController("config_files/51.json")
        self.browser_controller.update_signal.connect(self.update_output)
        self.action_signal.connect(self.browser_controller.perform_action)

        QTimer.singleShot(0, self.browser_controller.initialize_browser)

    def initUI(self):
        layout = QVBoxLayout()

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        input_layout = QHBoxLayout()
        self.input_line = QLineEdit()
        self.input_line.returnPressed.connect(self.send_command)
        input_layout.addWidget(self.input_line)

        send_button = QPushButton("Send")
        send_button.clicked.connect(self.send_command)
        input_layout.addWidget(send_button)

        layout.addLayout(input_layout)

        self.setLayout(layout)
        self.setWindowTitle('Browser Automation Chat')
        self.setGeometry(300, 300, 800, 600)

    def send_command(self):
        command = self.input_line.text()
        self.input_line.clear()
        self.action_signal.emit(command)

    @pyqtSlot(str)
    def update_output(self, text):
        self.output_text.append(text)
        self.output_text.append("\n")
        self.output_text.verticalScrollBar().setValue(self.output_text.verticalScrollBar().maximum())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = BrowserAutomationGUI()
    ex.show()
    sys.exit(app.exec_())