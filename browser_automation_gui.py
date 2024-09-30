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
        prompt = f"""
            You are a helpful web assistant helping human performing tasks. You will get a picture of the web page, and the general thing people want to do. You should give suggestions for the actions to achieve the thing described. 
            Description: {action_text}
        """

        action_prompt = {
            "intro": """You are an autonomous intelligent agent tasked with navigating a web browser. You will be given web-based tasks. These tasks will be accomplished through the use of specific actions you can issue.

        Here's the information you'll have:
        The user's objective: This is the task you're trying to complete.
        The current web page's accessibility tree: This is a simplified representation of the webpage, providing key information.
        The current web page's URL: This is the page you're currently navigating.
        The open tabs: These are the tabs you have open.
        The previous action: This is the action you just performed. It may be helpful to track your progress.

        The actions you can perform fall into several categories:

        Page Operation Actions:
        `click [id]`: This action clicks on an element with a specific id on the webpage.
        `type [id] [content] [press_enter_after=0|1]`: Use this to type the content into the field with id. By default, the "Enter" key is pressed after typing unless press_enter_after is set to 0.
        `hover [id]`: Hover over an element with id.
        `press [key_comb]`:  Simulates the pressing of a key combination on the keyboard (e.g., Ctrl+v).
        `scroll [direction=down|up]`: Scroll the page up or down.

        Tab Management Actions:
        `new_tab`: Open a new, empty browser tab.
        `tab_focus [tab_index]`: Switch the browser's focus to a specific tab using its index.
        `close_tab`: Close the currently active tab.

        URL Navigation Actions:
        `goto [url]`: Navigate to a specific URL.
        `go_back`: Navigate to the previously viewed page.
        `go_forward`: Navigate to the next page (if a previous 'go_back' action was performed).

        Completion Action:
        `stop [answer]`: Issue this action when you believe the task is complete. If the objective is to find a text-based answer, provide the answer in the bracket.

        Homepage:
        If you want to visit other websites, check out the homepage at http://homepage.com. It has a list of websites you can visit.
        http://homepage.com/password.html lists all the account name and password for the websites. You can use them to log in to the websites.

        To be successful, it is very important to follow the following rules:
        1. You should only issue an action that is valid given the current observation
        2. You should only issue one action at a time.
        4. Generate the action in the correct format, wrap the action inside ``````. For example, ```click [1234]```".
        5. Issue stop action when you think you have achieved the objective.""",
            "examples": [
                (
                    """OBSERVATION:
        [1744] link 'HP CB782A#ABA 640 Inkjet Fax Machine (Renewed)'
                [1749] StaticText '$279.49'
                [1757] button 'Add to Cart'
                [1760] button 'Add to Wish List'
                [1761] button 'Add to Compare'
        URL: http://onestopmarket.com/office-products/office-electronics.html
        OBJECTIVE: What is the price of HP Inkjet Fax Machine
        PREVIOUS ACTION: None""",
                    "```stop [$279.49]```",
                ),
                (
                    """OBSERVATION:
        [164] textbox 'Search' focused: True required: False
        [171] button 'Go'
        [174] link 'Find directions between two points'
        [212] heading 'Search Results'
        [216] button 'Close'
        URL: http://openstreetmap.org
        OBJECTIVE: Show me the restaurants near CMU
        PREVIOUS ACTION: None""",
                    "```type [164] [restaurants near CMU] [1]```",
                ),
            ],
            "template": """OBSERVATION:
        {observation}
        URL: {url}
        OBJECTIVE: {objective}
        PREVIOUS ACTION: {previous_action}""",
            "meta_data": {
                "observation": "accessibility_tree",
                "action_type": "id_accessibility_tree",
                "keywords": ["url", "objective", "observation", "previous_action"],
                "prompt_constructor": "CoTPromptConstructor",
                "answer_phrase": "In summary, the next action I will perform is",
                "action_splitter": "```"
            },
        }
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