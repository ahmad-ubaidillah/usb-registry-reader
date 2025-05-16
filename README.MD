# USB Registry Forensic Tool

A lightweight Python GUI tool to extract USB-related information from a Windows `NTUSER.DAT` / registry hive. Ideal for basic forensic analysis and digital investigations.

## 🔧 Requirements

- Python 3.8 or higher

## 📦 Installation & Usage

1. **Clone this repository and navigate into the project folder:**

   ```bash
   git clone https://github.com/your-username/usb-registry-reader.git
   cd usb-registry-reader
   ```

2. **Create and activate a virtual environment:**
   ```bash
    python3 -m venv venv
    # Activate on Windows:
    venv\Scripts\activate
    # Activate on macOS/Linux:
    source venv/bin/activate
   ```

3. **Install the dependencies:**

   ```bash
    pip3 install -r requirements.txt
   ```

4. **Install tkinter on Linux / Mac (Optional, If you doesn't have it):**

   ```bash
   sudo apt update
   sudo apt install python3-tk
   ```

5. **Run the tool:**

   ```bash
    python usb-registry-reader.py
   ```


5. **Instructions:**
	•	A GUI window will appear.
	•	Click the “Open .hiv/.dat File” button.
	•	Select a valid NTUSER.DAT / .HIV file.
	•	The tool will parse the registry and display information about connected USB devices in the table.
	•	Some information about the application also will save into registry_reader.log