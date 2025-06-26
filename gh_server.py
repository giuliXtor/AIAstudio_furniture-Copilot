from flask import Flask, request, jsonify
import sys              # UI add-ons
import threading
from server.config import *
from llm_calls import *
from ui_pyqt import FlaskClientChatUI       # UI add-on
from PyQt5.QtWidgets import QApplication    # UI add-on

app = Flask(__name__)
message = None

# -------------------- ROUTE 1: FROM UI --------------------
@app.route('/send_to_grasshopper', methods=['POST', 'GET'])  
def send_to_grasshopper():  
    global message

    if request.method == 'POST':
        data = request.get_json()
        message = data.get("preferences_text", "")

    print(f"Received from UI: {message}")
    
    result = extract_activities(message)
    print("Extracted activities result:", result)

    return jsonify({
        "response": f"Received message: {message}", 
        "activities": result
    })

# -------------------- ROUTE 2: FROM GRASSHOPPER --------------------
@app.route('/extract_activities', methods=['POST'])
def api_extract_activities():
    data = request.get_json()
    prompt = data.get("prompt", "")

    result = extract_activities(prompt)

    return jsonify({
        "activities_json": result.get("activities_json", []),
        "hourly_metabolic_rates": result.get("hourly_metabolic_rates", []),
        "hourly_activities": result.get("hourly_activities", []),
        "hourly_furniture": result.get("hourly_furniture", [])
    })

# -------------------- FLASK THREAD + PYQT UI --------------------
def run_flask():                        
    app.run(debug=True, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    app = QApplication(sys.argv)
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
