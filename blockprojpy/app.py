from flask import Flask, jsonify, render_template, request, redirect, url_for, flash
import os
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from web3 import Web3
import webbrowser
import logging

if not os.environ.get('PRIVATE_KEY'):
    print("Warning: PRIVATE_KEY not set in environment variables")

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# הגדרת Flask-Login לניהול תהליכי כניסה ויציאה של משתמשים
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# פרטי התחברות קבועים למנהל
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = generate_password_hash('admin123')

# שמירת הכתובת של המשתמש המחובר
user_address = None

# ABI וכתובת החוזה החכם מה-Remix
abi = [
	{
		"inputs": [],
		"stateMutability": "nonpayable",
		"type": "constructor"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "doctorAddress",
				"type": "address"
			},
			{
				"internalType": "string",
				"name": "_doctorId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_username",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_password",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_specialty",
				"type": "string"
			}
		],
		"name": "addDoctor",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_name",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "_dosage",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_stock",
				"type": "uint256"
			}
		],
		"name": "addMedication",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_patientId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_name",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "_age",
				"type": "uint256"
			},
			{
				"internalType": "string",
				"name": "_addressPatient",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_hmo",
				"type": "string"
			}
		],
		"name": "addPatient",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_patientId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_doctorId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "_treatmentDetails",
				"type": "string"
			}
		],
		"name": "addRecord",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "admin",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "doctorAddresses",
		"outputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "",
				"type": "address"
			}
		],
		"name": "doctors",
		"outputs": [
			{
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "username",
				"type": "string"
			},
			{
				"internalType": "bytes32",
				"name": "passwordHash",
				"type": "bytes32"
			},
			{
				"internalType": "string",
				"name": "specialty",
				"type": "string"
			},
			{
				"internalType": "bool",
				"name": "isAuthorized",
				"type": "bool"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getDoctors",
		"outputs": [
			{
				"internalType": "address[]",
				"name": "",
				"type": "address[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getMedications",
		"outputs": [
			{
				"components": [
					{
						"internalType": "string",
						"name": "name",
						"type": "string"
					},
					{
						"internalType": "uint256",
						"name": "dosage",
						"type": "uint256"
					},
					{
						"internalType": "uint256",
						"name": "stock",
						"type": "uint256"
					}
				],
				"internalType": "struct MedicalRecords.Medication[]",
				"name": "",
				"type": "tuple[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_patientId",
				"type": "string"
			}
		],
		"name": "getPatient",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "getPatientIds",
		"outputs": [
			{
				"internalType": "string[]",
				"name": "",
				"type": "string[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "_patientId",
				"type": "string"
			}
		],
		"name": "getRecords",
		"outputs": [
			{
				"components": [
					{
						"internalType": "string",
						"name": "patientId",
						"type": "string"
					},
					{
						"internalType": "string",
						"name": "doctorId",
						"type": "string"
					},
					{
						"internalType": "string",
						"name": "treatmentDetails",
						"type": "string"
					},
					{
						"internalType": "uint256",
						"name": "timestamp",
						"type": "uint256"
					}
				],
				"internalType": "struct MedicalRecords.Record[]",
				"name": "",
				"type": "tuple[]"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "medicationCounter",
		"outputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "medications",
		"outputs": [
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "dosage",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "stock",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "patientIds",
		"outputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			}
		],
		"name": "patients",
		"outputs": [
			{
				"internalType": "string",
				"name": "name",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "age",
				"type": "uint256"
			},
			{
				"internalType": "string",
				"name": "addressPatient",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "hmo",
				"type": "string"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "string",
				"name": "",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "",
				"type": "uint256"
			}
		],
		"name": "records",
		"outputs": [
			{
				"internalType": "string",
				"name": "patientId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "doctorId",
				"type": "string"
			},
			{
				"internalType": "string",
				"name": "treatmentDetails",
				"type": "string"
			},
			{
				"internalType": "uint256",
				"name": "timestamp",
				"type": "uint256"
			}
		],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "address",
				"name": "doctorAddress",
				"type": "address"
			}
		],
		"name": "removeDoctor",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{
				"internalType": "uint256",
				"name": "_id",
				"type": "uint256"
			},
			{
				"internalType": "uint256",
				"name": "_newStock",
				"type": "uint256"
			}
		],
		"name": "updateMedicationStock",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	}
]

contract_address = '0x97798a47094371c8B200fcdA59dB2F3E61f11098'
# חיבור ל-Ganache אוטומטית
def connect_ganache():
    try:
        w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:7545'))
        if not w3.is_connected():
            raise ConnectionError("Failed to connect to Ganache.")
        print("Connected to Ganache.")
        return w3
    except Exception as e:
        print(f"Ganache connection error: {e}")
        return None

# חיבור ל-MetaMask לפי דרישה
def connect_metamask():
    try:
        w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
        if not w3.is_connected():
            raise ConnectionError("Failed to connect to MetaMask.")
        print("Connected to MetaMask.")
        return w3
    except Exception as e:
        print(f"MetaMask connection error: {e}")
        return None

# פונקציה לבחירת חיבור לפי מה שנבחר אחרון
def get_web3_instance(provider='ganache'):
    if provider == 'metamask':
        return connect_metamask()
    return connect_ganache()  # ברירת מחדל ל-Ganache

# חיבור אוטומטי ל-Ganache עם עליית השרת
w3 = connect_ganache()

# הערכת גז דינמי לטרנזקציה
def get_dynamic_gas_limit(w3, tx):
    try:
        gas_estimate = w3.eth.estimate_gas(tx)
        print(f"Estimated gas: {gas_estimate}")
        return gas_estimate
    except Exception as e:
        print(f"Failed to estimate gas: {e}")
        return 300000  # ערך ברירת מחדל

# חתימת ושליחת טרנזקציה
def sign_transaction(w3, tx):
    try:
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise ValueError("Private key not set in environment.")

        print(f"Signing transaction with nonce: {tx['nonce']}")
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key=private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        print(f"Transaction sent with hash: {tx_hash.hex()}")
        return tx_hash
    except Exception as e:
        print(f"Failed to sign or send transaction: {e}")
        raise
    
# מחלקת User לניהול משתמשים ב-LoginManager
class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(username):
    if username == ADMIN_USERNAME:
        return User(username)
    return None

# פונקציה להוספת רשומה רפואית לבלוקצ'יין
def add_treatment_record(patient_id, name, doctor_id, treatment_details, provider_type='ganache'):
    try:
        w3 = get_web3_instance(provider_type)
        contract = w3.eth.contract(address=contract_address, abi=abi)

        tx_hash = contract.functions.addRecord(
            patient_id, name, doctor_id, treatment_details
        ).transact({
            'from': w3.eth.accounts[0],
            'gas': 200000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash('Treatment record added to blockchain.', 'success')
    except Exception as e:
        flash(f'Failed to add treatment record: {e}', 'danger')

def check_balance(w3):
    balance = w3.eth.get_balance(w3.eth.accounts[0])
    balance_in_eth = w3.fromWei(balance, 'ether')
    return balance_in_eth

# פונקציה להוספת תרופה לבלוקצ'יין
def add_medication(name, dosage, stock):
    try:
        contract = w3.eth.contract(address=contract_address, abi=abi)
        tx = contract.functions.addMedication(name, dosage, stock).build_transaction({
            'from': w3.eth.accounts[0],
            'nonce': w3.eth.get_transaction_count(w3.eth.accounts[0]),
            'gas': get_dynamic_gas_limit(w3, {}),
            'gasPrice': w3.eth.gas_price
        })

        tx_hash = sign_transaction(w3, tx)
        flash('Medication added to blockchain.', 'success')
    except Exception as e:
        flash(f'Failed to add medication: {e}', 'danger')

def is_valid_id(patient_id):
    return patient_id.isdigit() and len(patient_id) == 9

def is_valid_phone(phone):
    return phone.isdigit() and len(phone) == 10

logging.basicConfig(level=logging.DEBUG)

# פונקציה להוספת רופא לבלוקצ'יין
def add_doctor_to_blockchain(doctor_address, doctor_id, username, password, specialty):
    try:
        w3 = get_web3_instance('ganache')
        contract = w3.eth.contract(address=contract_address, abi=abi)

        # וידוא כתובת Checksum
        doctor_address = Web3.to_checksum_address(doctor_address)

        print(f"Adding doctor with address: {doctor_address}")
        print(f"ID: {doctor_id}, Username: {username}, Specialty: {specialty}")

        # בניית הטרנזקציה
        tx = contract.functions.addDoctor(
            doctor_address, doctor_id, username, password, specialty
        ).build_transaction({
            'from': w3.eth.accounts[0],
            'gas': 300000,  # ודא שהגז מספיק
            'gasPrice': w3.to_wei('20', 'gwei'),
            'nonce': w3.eth.get_transaction_count(w3.eth.accounts[0]),
        })

        # חתימה ושליחה של הטרנזקציה
        tx_hash = sign_transaction(w3, tx)
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

        print(f"Transaction successful with hash: {receipt.transactionHash.hex()}")
        flash('Doctor added successfully!', 'success')

    except ValueError as ve:
        print(f"ValueError: {ve}")
        flash(f"ValueError: {ve}", 'danger')
    except Exception as e:
        print(f"General error: {e}")
        flash(f"Error adding doctor: {e}", 'danger')
        
def authenticate_doctor(username, password, provider_type='ganache'):
    try:
        w3 = get_web3_instance(provider_type)
        contract = w3.eth.contract(address=contract_address, abi=abi)

        # יצירת האש של הסיסמה שהוזנה
        password_hash = w3.keccak(text=password)

        # שליפת פרטי הרופא מהחוזה לפי שם משתמש
        doctor = contract.functions.doctors(username).call()

        if doctor[2] == password_hash.hex():  # השוואת ההאש של הסיסמה
            return True  # אימות הצליח
        else:
            return False  # אימות נכשל
    except Exception as e:
        flash(f'Authentication failed: {e}', 'danger')
        return False
    

@app.route('/get_patient/<patient_id>')
def get_patient(patient_id):
    try:
        w3 = get_web3_instance('ganache')
        contract = w3.eth.contract(address=contract_address, abi=abi)
        patient_records = contract.functions.getRecords(patient_id).call()

        return render_template('patient_details.html', records=patient_records)
    except Exception as e:
        flash(f'Failed to get patient details: {e}', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    
@app.route('/edit_medication/<int:id>', methods=['POST'])
@login_required
def edit_medication(medication_id, new_stock):
    try:
        w3 = get_web3_instance('ganache')
        contract = w3.eth.contract(address=contract_address, abi=abi)
        tx_hash = contract.functions.updateMedicationStock(medication_id, new_stock).transact({
            'from': w3.eth.accounts[0],
            'gas': 200000
        })
        w3.eth.wait_for_transaction_receipt(tx_hash)
        flash('Medication stock updated successfully.', 'success')
    except Exception as e:
        flash(f'Failed to update medication stock: {e}', 'danger')
        

@app.route('/connect_provider', methods=['POST'])
def connect_provider():
    provider_type = request.form.get('provider_type')
    w3 = get_web3_instance(provider_type)
    if w3:
        flash(f'Connected to {provider_type} successfully!', 'success')
    else:
        flash(f'Failed to connect to {provider_type}.', 'danger')
    return redirect(url_for('admin_dashboard'))

# פונקציית התחברות לרופא או אדמין
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # אימות כאדמין
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD, password):
            user = User(username)
            login_user(user)
            return redirect(url_for('admin_dashboard'))

        # אימות כרופא
        elif authenticate_doctor(username, password):
            user = User(username)
            login_user(user)
            return redirect(url_for('doctor_dashboard'))

        flash('Login failed. Invalid username or password.', 'danger')

    return render_template('login.html')

# פונקציה ללוח הבקרה של האדמין
@app.route('/admin_dashboard', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.id != ADMIN_USERNAME:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # לוגיקה להוספת תרופה
        if 'add_medication' in request.form:
            name = request.form['medication_name']
            dosage = request.form['dosage']
            stock = request.form['stock']
            # קריאה לפונקציה להוספת תרופה
            add_medication(name, int(dosage), int(stock), provider_type=request.form.get('provider_type', 'ganache'))

        # לוגיקה לעריכת מלאי תרופות
        elif 'edit_medication' in request.form:
            medication_id = request.form['medication_id']
            new_stock = request.form['new_stock']
            # קריאה לפונקציה לעריכת המלאי של תרופה
            edit_medication(int(medication_id), int(new_stock))

    # שליפת רופאים, מטופלים ותרופות להצגה בלוח הבקרה
    doctors = get_all_doctors()
    patients = get_all_patients()
    medications = get_all_medications()

    return render_template('admin_dashboard.html', doctors=doctors, patients=patients, medications=medications)

@app.route('/add_doctor', methods=['POST'])
@login_required
def add_doctor_route():
    doctor_address = request.form.get('doctor_address', '').strip()
    doctor_id = request.form.get('doctor_id', '').strip()
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    specialty = request.form.get('specialty', '').strip()
	

    if not all([doctor_address, doctor_id, username, password, specialty]):
        flash('All fields are required', 'danger')
        return redirect(url_for('admin_dashboard'))

    message, category = add_doctor_to_blockchain(doctor_address, doctor_id, username, password, specialty)
    flash(message, category)

    return redirect(url_for('admin_dashboard'))

# פונקציות לשליפת כל הרופאים, המטופלים והתרופות
def get_all_doctors():
    try:
        w3 = get_web3_instance('ganache')
        if w3 is None:
            raise ConnectionError("Failed to connect to blockchain.")

        contract = w3.eth.contract(address=contract_address, abi=abi)
        doctor_list = contract.functions.getDoctors().call()
        return doctor_list
    except Exception as e:
        flash(f'Failed to get doctors: {e}', 'danger')
        return []

def get_all_medications():
    try:
        w3 = get_web3_instance('ganache')
        contract = w3.eth.contract(address=contract_address, abi=abi)
        medications = contract.functions.getMedications().call()
        return medications
    except Exception as e:
        flash(f'Failed to get medications: {e}', 'danger')
        return []
    
def get_all_patients():
    try:
        w3 = get_web3_instance('ganache')
        if w3 is None:
            raise ConnectionError("Failed to connect to blockchain.")

        contract = w3.eth.contract(address=contract_address, abi=abi)
        patient_ids = contract.functions.getPatientIds().call()

        patients = []
        for patient_id in patient_ids:
            data = contract.functions.getPatient(patient_id).call()
            patient = {
                'ID': patient_id,
                'Name': data[0],
                'Age': data[1],
                'Address': data[2],
                'HMO': data[3]
            }
            patients.append(patient)

        return patients
    except Exception as e:
        flash(f'Failed to get patients: {e}', 'danger')
        return []

@app.route('/connect_metamask', methods=['POST'])
def connect_metamask():
    global user_address
    try:
        data = request.get_json()
        user_address = data.get('address')  # קבלת הכתובת מהלקוח
        if user_address:
            return jsonify({"message": "Connected to MetaMask successfully!", "success": True})
        else:
            return jsonify({"message": "Failed to connect MetaMask. No address received.", "success": False})
    except Exception as e:
        return jsonify({"message": f"Error: {e}", "success": False})
    
# עמוד רופא
@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    return render_template('doctor_dashboard.html')

# יציאה מהמערכת
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))


print(f"Contract Address: {contract_address}")
print(f"Using account: {w3.eth.accounts[0]}")

# פונקציה לפתיחת הדפדפן
def open_browser():
    webbrowser.open_new("http://127.0.0.1:5000/")

if __name__ == "__main__":
    from threading import Timer
    Timer(1, open_browser).start()
    app.run(debug=True)