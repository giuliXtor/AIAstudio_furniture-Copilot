import sys
print (sys.version)
import requests
from llm_calls import *
from PyQt5.QtWidgets import (
    QTextEdit, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextBrowser, QHBoxLayout
)


class FlaskClientChatUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant")
        self.setGeometry(200, 200, 800, 800)

        # Main layout
        layout = QVBoxLayout()

        # Chat display area
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        layout.addWidget(self.chat_display)

        # Add welcome message
        self.chat_display.append("<b>Assistant:</b> Welcome! Would you like some advice to furnish your living room? If you tell me about your daily routine, I can help you place the right furniture in the right place!")

        # Input and send button layout
        input_layout = QHBoxLayout()

        # multi lines input field for user messages
        self.input_field = QTextEdit()
        self.input_field.setPlaceholderText(
        "Please enter a message...\ne.g. I work from 8am to 4pm, read 6–8pm, yoga at 9pm, sleep 11–7am"
        )
        self.input_field.setMaximumHeight(100)  # Limit height for better UI/about 4 lines with 14px height font
        
        # # single line input field for user messages
        # self.input_field = QLineEdit()
        # self.input_field.setPlaceholderText("Type your message here...")

        input_layout.addWidget(self.input_field)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        layout.addLayout(input_layout)

        # Set central widget
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def send_message(self):
        # message = self.input_field.text().strip() # uncomment to go to single line input field
        message = self.input_field.toPlainText().strip() # uncomment to go to multi line input field

        if not message:
            self.chat_display.append("<span style='color: red;'>Please enter a message.</span>")
            return

        # Display the user's message in the chat window
        self.chat_display.append(f"<b>You:</b> {message}")
        self.input_field.clear()

        try:
            # Send the message to Flask in a POST request
            response = requests.post(
                "http://127.0.0.1:5000/send_to_grasshopper",
                json={"preferences_text": message}
            )
            response_data = response.json()

            # Optional debug log
            print("Raw server response:", response_data)

            # Display the server's response in the chat window
            self.chat_display.append("<b>Assistant:</b> Please wait while I am processing your input and building your metabolic routine...")
            # self.chat_display.append(f"<b>Assistant:</b> {response_data}") #changed to the above to avoid repeting the all message.

        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Error connecting to the server.</span>")
            print(f"Error: {e}")
