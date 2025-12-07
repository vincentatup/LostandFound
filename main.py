import sys
from PyQt6.QtWidgets import QApplication, QDialog
from database import Database
from ui import LoginDialog, DashboardWindow

def main():
    app = QApplication(sys.argv)
    
    # Initialize Database (creates 'lost_and_found.db')
    db = Database()
    
    login = LoginDialog(db)
    
    if login.exec() == QDialog.DialogCode.Accepted:
        # login.user_data contains (id, username, role)
        window = DashboardWindow(db, login.user_data)
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit()

if __name__ == "__main__":
    main()