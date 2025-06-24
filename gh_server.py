from flask import Flask, request, jsonify

import sys              #UI adds-on
import threading
from server.config import *
from llm_calls import *
# from PIL import ImageQt # Fix: Import ImageQt directly
from ui_pyqt import FlaskClientChatUI       #UI adds-on
from PyQt5.QtWidgets import QApplication    #UI adds-on

app = Flask(__name__)

message = None

#UIstart adds-on
@app.route('/send_to_grasshopper', methods=['POST', 'GET'])  
def send_to_grasshopper():  
    global message  # Use the global variable to store the message

    if request.method == 'POST':
        data = request.get_json()  # Retrieve the JSON object sent by the UI
        message = data["preferences_text"] # Expects a key named "message"
    
    print(f"Received from UI: {message}")

    result = extract_activities(message)
    print("Extracted activities result:", result)  # ✅ Debug line here
    
    return jsonify({"response": f"Received message: {message}", 
                    "activities": result
    })  # Return a JSON response with the message and activities

#UIend adds-on


@app.route('/extract_activities', methods=['POST'])
def api_extract_activities():
    data = request.get_json()
    prompt = data.get("prompt", "")
    
    result = extract_activities(prompt)
    
    return jsonify({"activities": result})


#UIstart adds-on
def run_flask():                        
    app.run(debug=True, use_reloader=False)  # Run Flask server in a separate thread

if __name__ == '__main__':
#    app.run(debug=True) #commented out UI adds-on 

    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start PyQt application
    app = QApplication(sys.argv)
    # app.setStyleSheet("QWidget { font-size: 14px; }") 
    app.setStyleSheet("""
    QWidget {
        background-color: #121212;
        color: #FFFFFF;
        font-size: 14px;
        font-family: "Roboto Mono";
    }
    QLineEdit {
        background-color: #1E1E1E;
        color: #FFFFFF;
        border: 1px solid #3A3A3A;
        padding: 4px;
        font-family: "Roboto Mono";
    }
    QTextBrowser {
        background-color: #1E1E1E;
        color: #FFFFFF;
        border: 1px solid #3A3A3A;
        font-family: "Roboto Mono";
    }
    QPushButton {
        background-color: #2D2D2D;
        color: #FFFFFF;
        border: 1px solid #3A3A3A;
        padding: 6px;
        font-family: "Roboto Mono";
    }
    QPushButton:hover {
        background-color: #3C3C3C;
    }
""")

    window = FlaskClientChatUI()
    window.show()
    sys.exit(app.exec_())
#UIend UI adds-on