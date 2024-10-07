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

            welcome_message = "Welcome to Browser Automation Chat!\n\n"
            welcome_message += "Available actions:\n"
            welcome_message += "- print: Prints current observation\n"
            welcome_message += "- click element_text: Click on an element\n"
            welcome_message += "- hover element_text: Hover over an element\n"
            welcome_message += "- type element_text [input_text]: Type text into an input field\n"
            welcome_message += "- scroll up/down: Scroll the page\n"
            welcome_message += "- press key_combination: Press a key or key combination\n"
            welcome_message += "- new_tab: Open a new tab\n"
            welcome_message += "- close_tab: Close the current tab\n"
            welcome_message += "- goto URL: Navigate to a specific URL\n"
            welcome_message += "- go_back: Go back to the previous page\n"
            welcome_message += "- go_forward: Go forward to the next page\n"
            welcome_message += "- tab_focus tab_number: Focus on a specific tab\n"
            welcome_message += "- stop answer: Stop the current task with an optional answer\n"
            self.update_signal.emit(welcome_message)
            self.update_signal.emit(f"Browser initialized. Current URL: {self.env.page.url}\n")

        except Exception as e:
            self.update_signal.emit(f"Error initializing browser: {str(e)}")

    def clean_text(self, text):
        # Remove non-printable characters and trim whitespace
        return re.sub(r'[^\x20-\x7E]+', '', text).strip()

    def find_element_id_by_text(self, text):
        lines = self.obs["text"].split('\n')
        exact_match = None
        partial_match = None
        
        cleaned_search_text = self.clean_text(text.lower())
        
        for line in lines:
            match = re.search(r'\[(\d+)\]\s+(\w+)\s+\'(.+?)\'', line)
            if match:
                element_id, element_type, element_text = match.groups()
                cleaned_element_text = self.clean_text(element_text.lower())
                
                if cleaned_search_text == cleaned_element_text:
                    exact_match = element_id
                    break
                elif cleaned_search_text in cleaned_element_text:
                    partial_match = element_id
        
        return exact_match or partial_match


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
            if action_text == "print":
                self.update_signal.emit(f"Observation:\n{self.obs['text']}")
            else:
                action = self.parse_action(action_text)
                
                # Get the current URL before the action
                before_url = self.env.page.url
                
                self.obs, reward, terminated, truncated, self.info = self.env.step(action)
                
                # Get the URL after the action
                after_url = self.env.page.url
                
                # Prepare the feedback message
                feedback = f"Performed action: {action_text}\n"
                feedback += f"Before URL: {before_url}\n"
                feedback += f"After URL: {after_url}\n"
                feedback += f"Reward: {reward}, Terminated: {terminated}, Truncated: {truncated}\n\n"
                # feedback += f"New Observation:\n{self.obs['text']}"
                
                self.update_signal.emit(feedback)
        except Exception as e:
            self.update_signal.emit(f"Error performing action: {str(e)}")

    def parse_action(self, action_text):
        action_text = action_text.strip().lower()
        
        if action_text.startswith("click "):
            element_text = action_text[6:]
            element_id = self.find_element_id_by_text(element_text)
            if element_id:
                return create_id_based_action(f"click [{element_id}]")
            else:
                raise ValueError(f"Element '{element_text}' not found")
        
        elif action_text.startswith("hover "):
            element_text = action_text[6:]
            element_id = self.find_element_id_by_text(element_text)
            if element_id:
                return create_id_based_action(f"hover [{element_id}]")
            else:
                raise ValueError(f"Element '{element_text}' not found")
        
        elif action_text.startswith("type "):
            match = re.match(r"type (.*?) \[(.*?)\]", action_text)
            if match:
                element_text, input_text = match.groups()
                element_id = self.find_element_id_by_text(element_text)
                if element_id:
                    return create_id_based_action(f"type [{element_id}] [{input_text}]")
                else:
                    raise ValueError(f"Element '{element_text}' not found")
            else:
                raise ValueError("Invalid type command format: type email [email@address.com]")
        
        elif action_text.startswith("scroll "):
            direction = action_text[7:]
            if direction in ["up", "down"]:
                return create_id_based_action(f"scroll [{direction}]")
            else:
                raise ValueError("Invalid scroll direction")
        
        elif action_text.startswith("press "):
            key_comb = action_text[6:]
            return create_id_based_action(f"press [{key_comb}]")
        
        elif action_text == "new_tab":
            return create_id_based_action("new_tab")
        
        elif action_text == "close_tab":
            return create_id_based_action("close_tab")
        
        elif action_text.startswith("goto "):
            url = action_text[5:]
            return create_id_based_action(f"goto [{url}]")
        
        elif action_text == "go_back":
            return create_id_based_action("go_back")
        
        elif action_text == "go_forward":
            return create_id_based_action("go_forward")
        
        elif action_text.startswith("tab_focus "):
            tab_number = action_text[10:]
            return create_id_based_action(f"tab_focus [{tab_number}]")
        
        elif action_text.startswith("stop "):
            answer = action_text[5:]
            return create_stop_action(answer)
        
        else:
            raise ValueError(f"Unknown action: {action_text}")

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