import sys
print (sys.version)
import requests
from llm_calls import *
from PyQt5.QtWidgets import (
    QTextEdit, QMainWindow, QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton, QTextBrowser, QHBoxLayout
)
from PyQt5.QtGui import QPixmap
import matplotlib.pyplot as plt
import io
from PIL import Image
from collections import OrderedDict
import pyqtgraph as pg
from pyqtgraph import PlotWidget
import numpy as np


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

            # get activities and MET data from the response
            # ✅ NEW: Get activity + MET data
            activities = response_data.get("activities", {})
            met_rates = activities.get("hourly_metabolic_rates", [])
            activity_labels = activities.get("hourly_activities", [])

            if not met_rates or not activity_labels:
                self.chat_display.append(
                    "<span style='color: red;'>No metabolic data returned. Please check your input or server logic.</span>"
                )
                print("Warning: Missing 'hourly_metabolic_rates' or 'hourly_activities' in response.")
                return

            # ✅ NEW: Plot it if data is valid
            if met_rates and activity_labels:
                self.display_met_graph(met_rates, activity_labels)

        except requests.exceptions.RequestException as req_err:
            self.chat_display.append("<span style='color: red;'>Network error connecting to the server.</span>")
            print(f"RequestException: {req_err}")

        except ValueError as json_err:
            self.chat_display.append("<span style='color: red;'>Server returned invalid JSON.</span>")
            print(f"JSON decode error: {json_err}")

        except Exception as e:
            self.chat_display.append("<span style='color: red;'>Unexpected error occurred.</span>")
            print(f"Unhandled Exception: {e}")

    def display_met_graph(self, met_rates, activities):
        print("📊 display_met_graph (pyqtgraph) was called!")

        # Maintain activity order
        unique_acts = list(OrderedDict.fromkeys(activities))
        colors = pg.intColor  # Function to assign consistent colors

        hours = list(range(25))
        met_steps = met_rates + [met_rates[-1]]

        # Optional: remove old plots
        layout = self.centralWidget().layout()
        for i in reversed(range(layout.count())):
            item = layout.itemAt(i).widget()
            if isinstance(item, PlotWidget):
                layout.removeWidget(item)
                item.deleteLater()

        # Create pyqtgraph widget
        plot_widget = PlotWidget()
        plot_widget.setBackground("#121212")
        plot_widget.setTitle("Hourly Metabolic Rates", color="w", size="14pt")
        plot_widget.setLabel("left", "MET")
        plot_widget.setLabel("bottom", "Hour")
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.addLegend(offset=(10, 10))

        # Tick every hour (X axis)
        plot_widget.getAxis("bottom").setTicks([[(h, str(h)) for h in range(25)]])

        # Tick every 0.5 MET (Y axis)
        y_ticks = [(y, f"{y:.1f}") for y in np.arange(0, 3.0, 0.5)]
        plot_widget.getAxis("left").setTicks([y_ticks])

        for i, act in enumerate(unique_acts):
            mask = [a == act for a in activities]
            values = [m if msk else None for m, msk in zip(met_steps, mask + [mask[-1]])]

            # pyqtgraph doesn't accept None, so set to np.nan
            y_vals = np.array(values, dtype=np.float32)
            y_vals[np.array([v is None for v in values])] = np.nan

            plot_widget.plot(
                x=hours,
                y=y_vals,
                pen=pg.mkPen(color=colors(i), width=2),
                name=act
            )

        plot_widget.setYRange(0, 2.5)
        plot_widget.setXRange(0, 24)

        layout.addWidget(plot_widget)
        print("📎 PlotWidget added to layout.")
 
        # except Exception as e:  # Uncomment this block to handle all exceptions
        #     self.chat_display.append("<span style='color: red;'>Error connecting to the server.</span>")
        #     print(f"Error: {e}")
