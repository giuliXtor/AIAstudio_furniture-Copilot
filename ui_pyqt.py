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
        self.setWindowTitle("Furnish Assistant")
        self.setGeometry(200, 200, 900, 900)

        # Main layout
        layout = QVBoxLayout()

        # Chat display area
        self.chat_display = QTextBrowser()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(300)
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

        # Add a dedicated container for the plot to avoid messing up layout
        self.plot_container = QWidget()
        self.plot_container.setMinimumHeight(600)  # Reserve space always
        self.plot_container.setMaximumHeight(600)  # Fix the height, so no resizing occurs
        self.plot_container_layout = QVBoxLayout()
        self.plot_container_layout.setContentsMargins(0,0,0,0)
        self.plot_container.setLayout(self.plot_container_layout)
        layout.addWidget(self.plot_container)

        # ---- MODIFICATION: Add a blank placeholder widget to reserve plot space at startup ----
        self.plot_placeholder = QWidget()
        self.plot_container_layout.addWidget(self.plot_placeholder)
        # ---------------------

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
            activity_data = response_data.get("activities", {})
            met_rates = activity_data.get("hourly_metabolic_rates", [])
            activity_labels = activity_data.get("hourly_activities", [])


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
   
    def get_continuous_intervals(self, activity_hours):
        intervals = []
        if not activity_hours:
            return intervals
        start = activity_hours[0]
        prev = start
        for h in activity_hours[1:]:
            if h != prev + 1:
                intervals.append((start, prev))
                start = h
            prev = h
        intervals.append((start, prev))
        return intervals

    def create_step_arrays(self, start, end, value):
        x = []
        y = []
        for h in range(start, end + 1):
            x.extend([h, h + 1])
            y.extend([value, value])
        return np.array(x), np.array(y)



    def display_met_graph(self, met_rates, activities):
        print("📊 display_met_graph (pyqtgraph) was called!")

    # Clear previous plots in plot container
        for i in reversed(range(self.plot_container_layout.count())):
            widget = self.plot_container_layout.itemAt(i).widget()
            if widget:
                self.plot_container_layout.removeWidget(widget)
                widget.deleteLater()

        unique_acts = list(OrderedDict.fromkeys(activities))
        colors = pg.intColor

        plot_widget = PlotWidget()
        plot_widget.setBackground("#121212")
        plot_widget.setTitle("Hourly Metabolic Rates", color="w", size="14pt")
        plot_widget.setLabel("left", "MET")
        plot_widget.setLabel("bottom", "Hour")
        plot_widget.showGrid(x=True, y=True, alpha=0.3)
        plot_widget.addLegend(offset=(10, 10))
        plot_widget.getAxis("bottom").setTicks([[(h, str(h)) for h in range(25)]])
        y_ticks = [(y, f"{y:.1f}") for y in np.arange(0, 3.0, 0.5)]
        plot_widget.getAxis("left").setTicks([y_ticks])
        plot_widget.setYRange(0, 2.5)
        plot_widget.setXRange(0, 24)

        legend = pg.LegendItem(offset=(0, 0))
        legend.setParentItem(plot_widget.getPlotItem())

        # Anchor to top-right of the plot
        legend.anchor((0, 0), (0, 0))  # (legend corner, plot corner)
        legend.setOffset((80, 10))      # x=20px to the right of the plot's right edge

        for i, act in enumerate(unique_acts):
            activity_hours = [idx for idx, a in enumerate(activities) if a == act]
            intervals = self.get_continuous_intervals(activity_hours)

            # We will store a single reference line for the legend
            legend_curve = None

            for (start, end) in intervals:
                met_value = met_rates[start]
                x_vals, y_vals = self.create_step_arrays(start, end, met_value)

                curve = plot_widget.plot(
                    x=x_vals,
                    y=y_vals,
                    pen=pg.mkPen(color=colors(i), width=4),
                    name=None  # Don't trigger auto-legend
                )

                if legend_curve is None:
                    legend_curve = curve

            # ✅ Add just one curve to legend (manually)
            legend.addItem(legend_curve, act)

        self.plot_container_layout.addWidget(plot_widget)
        print("📎 PlotWidget added to layout.")

 
