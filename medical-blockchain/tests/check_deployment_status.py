from web3 import Web3
from dotenv import load_dotenv
import os
import time

def check_deployment_status(tx_hash):
    load_dotenv()
    w3 = Web3(Web3.HTTPProvider(os.getenv('PROVIDER_URL')))
    
    print("בודק סטטוס התקנה...\n")
    print(f"Hash: {tx_hash}")
    
    try:
        max_attempts = 20
        for attempt in range(max_attempts):
            # קבלת קבלה
            tx_receipt = w3.eth.get_transaction_receipt(tx_hash)
            
            if tx_receipt is None:
                print(f"\rממתין לאישור הטרנזקציה... ניסיון {attempt + 1}/{max_attempts}", end='')
                time.sleep(5)
                continue
            
            print("\n\nפרטי הטרנזקציה:")
            print(f"סטטוס: {'✅ הצליח' if tx_receipt['status'] == 1 else '❌ נכשל'}")
            print(f"בלוק מספר: {tx_receipt['blockNumber']}")
            print(f"גז שנוצל: {tx_receipt['gasUsed']} ({(tx_receipt['gasUsed']/2764490)*100:.1f}% מהגז שהוקצה)")
            
            if tx_receipt['status'] == 1:
                contract_address = tx_receipt['contractAddress']
                print(f"\n🎉 החוזה הותקן בהצלחה!")
                print(f"כתובת החוזה: {contract_address}")
                
                # בדיקת קוד בכתובת
                code = w3.eth.get_code(contract_address)
                print(f"גודל קוד החוזה: {len(code)} bytes")
                
                # שמירת הכתובת ב-.env
                if not os.getenv('CONTRACT_ADDRESS'):
                    with open('.env', 'a') as f:
                        f.write(f'\nCONTRACT_ADDRESS={contract_address}')
                    print("✅ כתובת החוזה נשמרה בקובץ .env")
                
                # הצגת כתובת ה-etherscan לבדיקה
                print(f"\nניתן לראות את החוזה ב-Etherscan:")
                print(f"https://sepolia.etherscan.io/address/{contract_address}")
                
                return contract_address
            else:
                print("\n❌ התקנת החוזה נכשלה")
                return None
                
        print("\nתם הזמן המוקצב לאישור הטרנזקציה")
        return None
        
    except Exception as e:
        print(f"\nשגיאה בבדיקת הסטטוס: {str(e)}")
        return None

if __name__ == "__main__":
    tx_hash = "0x6fcf78d3247d47bcd699109ca3dfed8fa713070e66a511771bba8d019bc70d32"
    contract_address = check_deployment_status(tx_hash)
    
    if contract_address:
        print("\nהמערכת מוכנה לשימוש!")
        print("ניתן להתחיל להשתמש בחוזה")