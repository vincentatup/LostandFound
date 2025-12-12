from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QTableWidget, 
    QTableWidgetItem, QHeaderView, QComboBox, QTabWidget, 
    QDialog, QFormLayout, QGroupBox, QTextEdit, QFileDialog
)
from PyQt6.QtGui import QPixmap, QColor
from PyQt6.QtCore import Qt
import os

# --- LOGIN & REGISTER WINDOW ---
# This class handles the first window you see (Login/Register popup)
class LoginDialog(QDialog):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.user_data = None # This will store the user info if login is successful
        
        # Window settings
        self.setWindowTitle("Lost & Found Login")
        self.setFixedSize(300, 350)
        
        # We use tabs to switch between "Login" and "Register"
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        
        self.setup_login_tab()    # Builds the Login form
        self.setup_register_tab() # Builds the Register form
        
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # --- Setup Login Form ---
    def setup_login_tab(self):
        self.login_tab = QWidget()
        layout = QFormLayout()
        
        # Input fields for Login
        self.login_user = QLineEdit()
        self.login_pass = QLineEdit()
        self.login_pass.setEchoMode(QLineEdit.EchoMode.Password) # Hides text with stars (*)
        
        # The Login Button
        btn_login = QPushButton("Login")
        btn_login.clicked.connect(self.perform_login) # When clicked, run perform_login()
        
        layout.addRow("Username:", self.login_user)
        layout.addRow("Password:", self.login_pass)
        layout.addRow(btn_login)
        
        self.login_tab.setLayout(layout)
        self.tabs.addTab(self.login_tab, "Login")

    # --- Setup Register Form ---
    def setup_register_tab(self):
        self.reg_tab = QWidget()
        layout = QFormLayout()
        
        # Input fields for Registration
        self.reg_user = QLineEdit()
        self.reg_pass = QLineEdit()
        self.reg_pass.setEchoMode(QLineEdit.EchoMode.Password)
        
        # Dropdown to choose role (User or Admin)
        self.reg_role = QComboBox()
        self.reg_role.addItems(["User", "Admin"])
        
        # The Register Button
        btn_reg = QPushButton("Create Account")
        btn_reg.clicked.connect(self.perform_register) # When clicked, run perform_register()
        
        layout.addRow("Username:", self.reg_user)
        layout.addRow("Password:", self.reg_pass)
        layout.addRow("Role:", self.reg_role)
        layout.addRow(btn_reg)
        
        self.reg_tab.setLayout(layout)
        self.tabs.addTab(self.reg_tab, "Register")

    # --- Logic: Clicking Login Button ---
    def perform_login(self):
        username = self.login_user.text()
        password = self.login_pass.text()
        
        # Check database for this user
        user = self.db.login_user(username, password)
        if user:
            self.user_data = user # Save user data to pass to the Dashboard
            self.accept()         # Close this window and open the main app
        else:
            QMessageBox.warning(self, "Error", "Invalid username or password")

    # --- Logic: Clicking Create Account Button ---
    def perform_register(self):
        username = self.reg_user.text()
        password = self.reg_pass.text()
        role = self.reg_role.currentText()
        
        # Basic validation to make sure fields aren't empty
        if not username or not password:
            QMessageBox.warning(self, "Error", "All fields are required")
            return

        # Try to save to database
        if self.db.register_user(username, password, role):
            QMessageBox.information(self, "Success", "Account created! Please login.")
            self.tabs.setCurrentIndex(0) # Automatically switch back to Login tab
        else:
            QMessageBox.warning(self, "Error", "Username already exists")

# --- MAIN DASHBOARD WINDOW ---
# This is the main application window that opens after login
class DashboardWindow(QMainWindow):
    def __init__(self, db_manager, user_data):
        super().__init__()
        self.db = db_manager
        # Unpack user data: ID, Username, and Role (Admin/User)
        self.user_id, self.username, self.role = user_data
        self.current_image_path = "" 
        
        self.setWindowTitle(f"Lost & Found Board - {self.username}")
        self.resize(1100, 750)
        
        # Main layout container
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.layout = QVBoxLayout(central_widget)
        
        self.setup_ui()   # Draw the interface
        self.load_data()  # Fetch items from database

    # --- Build the User Interface ---
    def setup_ui(self):
        # 1. TOP BAR: Shows the welcome message
        top_bar = QHBoxLayout()
        role_label = QLabel(f"Welcome, {self.username} ({self.role})")
        role_label.setStyleSheet("font-weight: bold; font-size: 16px;") 
        top_bar.addWidget(role_label)
        top_bar.addStretch()
        self.layout.addLayout(top_bar)

        # 2. FORM AREA: Where you type in item details
        form_group = QGroupBox() 
        main_form_layout = QHBoxLayout()
        
        # -- Left Side: Text Inputs (Name, Contact, Desc) --
        input_layout = QFormLayout()
        
        self.status_input = QComboBox()
        self.status_input.addItems(["Lost", "Found"]) # Initial status options
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g., Black iPhone 12, Golden Retriever")
        
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Phone number or Email")

        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("Detailed description...")
        self.desc_input.setMaximumHeight(60)

        # Button to choose a picture file
        self.img_btn = QPushButton("Upload Image")
        self.img_btn.clicked.connect(self.select_image)

        # Button to save the new item to database
        add_btn = QPushButton("Post Item")
        add_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 5px;")
        add_btn.clicked.connect(self.add_item)

        # Add all inputs to the form layout
        input_layout.addRow("Status:", self.status_input)
        input_layout.addRow("Item Name:", self.name_input)
        input_layout.addRow("Contact Info:", self.contact_input)
        input_layout.addRow("Description:", self.desc_input)
        input_layout.addRow("Image:", self.img_btn)
        input_layout.addRow(add_btn)
        
        # -- Right Side: Image Preview Box --
        self.image_preview = QLabel("No Image Selected")
        self.image_preview.setFixedSize(200, 200)
        self.image_preview.setStyleSheet("border: 1px dashed gray; background-color: #f0f0f0; color: black;")
        self.image_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_preview.setScaledContents(True)

        # Combine Left (Inputs) and Right (Image)
        container_left = QWidget()
        container_left.setLayout(input_layout)
        
        main_form_layout.addWidget(container_left, stretch=2)
        main_form_layout.addWidget(self.image_preview, stretch=1)
        
        form_group.setLayout(main_form_layout)
        self.layout.addWidget(form_group)

        # 3. TABLE AREA: Displays the list of items
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Status", "Item", "Description", "Contact", "Posted By"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        # When you click a row, fill the form with that item's data
        self.table.itemClicked.connect(self.populate_form_from_table)
        
        self.layout.addWidget(self.table)

        # 4. ACTION BUTTONS (Bottom Row)
        btn_layout = QHBoxLayout()
        
        # "Mark as Returned" Button (Blue)
        self.resolve_btn = QPushButton("Mark as Returned")
        self.resolve_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.resolve_btn.clicked.connect(self.mark_as_returned)

        # "Update Info" Button (Standard)
        update_btn = QPushButton("Update Info")
        update_btn.clicked.connect(self.update_item)
        
        # "Delete Post" Button (Red)
        delete_btn = QPushButton("Delete Post")
        delete_btn.setStyleSheet("background-color: #f44336; color: white;")
        delete_btn.clicked.connect(self.delete_item)
        
        # "Clear Form" Button (Standard)
        clear_btn = QPushButton("Clear Form")
        clear_btn.clicked.connect(self.clear_form)
        
        # "Refresh" Button
        refresh_btn = QPushButton("Refresh List")
        refresh_btn.clicked.connect(self.load_data)
        
        # Add buttons to the layout
        btn_layout.addWidget(self.resolve_btn)
        btn_layout.addWidget(update_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch() # Adds a spacer to push Refresh to the right
        btn_layout.addWidget(refresh_btn)
        
        self.layout.addLayout(btn_layout)

    # --- Logic: Upload Image Button ---
    def select_image(self):
        # Opens a file dialog to pick an image
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if file_name:
            self.current_image_path = file_name
            self.display_image(file_name)

    # Helper: Displays the image in the box on the right
    def display_image(self, path):
        if path and os.path.exists(path):
            pixmap = QPixmap(path)
            self.image_preview.setPixmap(pixmap)
        else:
            self.image_preview.setText("No Image Available")
            self.image_preview.setStyleSheet("border: 1px dashed gray; background-color: #f0f0f0; color: black;")

    # --- Logic: Load Data into Table ---
    def load_data(self):
        self.table.setRowCount(0) # Clear existing rows
        items = self.db.get_items(self.user_id, self.role) # Fetch from DB
        
        for row_idx, row_data in enumerate(items):
            self.table.insertRow(row_idx)
            
            # row_data: (id, name, description, status, contact, image_path, username, owner_id)
            status_text = row_data[3]
            status_item = QTableWidgetItem(status_text)
            
            # --- Status Color Logic ---
            if status_text == "Lost":
                status_item.setForeground(Qt.GlobalColor.red)
            elif status_text == "Found":
                status_item.setForeground(Qt.GlobalColor.darkGreen)
            elif status_text == "Returned":
                status_item.setForeground(Qt.GlobalColor.gray)

            # Insert data into columns
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(row_data[0]))) # ID
            self.table.setItem(row_idx, 1, status_item)                       # Status
            self.table.setItem(row_idx, 2, QTableWidgetItem(row_data[1]))     # Name
            self.table.setItem(row_idx, 3, QTableWidgetItem(row_data[2]))     # Desc
            self.table.setItem(row_idx, 4, QTableWidgetItem(row_data[4]))     # Contact
            self.table.setItem(row_idx, 5, QTableWidgetItem(row_data[6]))     # Username
            
            # Store hidden data (Owner ID and Image Path) for logic use
            self.table.item(row_idx, 0).setData(Qt.ItemDataRole.UserRole, row_data[7]) # owner_id
            self.table.item(row_idx, 1).setData(Qt.ItemDataRole.UserRole, row_data[5]) # image_path

    # --- Logic: Click a Table Row ---
    def populate_form_from_table(self, item):
        row = item.row()
        
        # Set the dropdown status
        status_text = self.table.item(row, 1).text()
        index = self.status_input.findText(status_text)
        if index >= 0:
            self.status_input.setCurrentIndex(index)
            
        # Fill text boxes
        self.name_input.setText(self.table.item(row, 2).text())
        self.desc_input.setText(self.table.item(row, 3).text())
        self.contact_input.setText(self.table.item(row, 4).text())
        
        # Retrieve hidden image path and display it
        img_path = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        self.current_image_path = img_path if img_path else ""
        self.display_image(self.current_image_path)

    # Helper: Check if current user is allowed to edit this row
    def check_permission(self, row_idx):
        if self.role == "Admin":
            return True # Admins can edit anything
        
        # Get the owner_id hidden in the row
        owner_id = self.table.item(row_idx, 0).data(Qt.ItemDataRole.UserRole)
        # Check if it matches logged-in user
        return owner_id == self.user_id

    # --- Logic: "Post Item" Button ---
    def add_item(self):
        name = self.name_input.text()
        if not name:
            QMessageBox.warning(self, "Error", "Item Name is required")
            return
            
        # Send data to database
        self.db.add_item(name, self.desc_input.toPlainText(), 
                         self.status_input.currentText(), self.contact_input.text(), 
                         self.current_image_path, self.user_id)
        self.load_data()  # Refresh table
        self.clear_form() # Reset inputs
        QMessageBox.information(self, "Success", "Item Posted!")

    # --- Logic: "Update Info" Button ---
    def update_item(self):
        current_row = self.table.currentRow()
        if current_row < 0: return # No row selected

        if not self.check_permission(current_row):
            QMessageBox.critical(self, "Denied", "You can only edit your own posts.")
            return

        # Ask for confirmation
        reply = QMessageBox.question(self, 'Confirm Update', 'Update this item details?',
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            item_id = self.table.item(current_row, 0).text()
            self.db.update_item(
                item_id, self.name_input.text(), self.desc_input.toPlainText(), 
                self.status_input.currentText(), self.contact_input.text(), self.current_image_path
            )
            self.load_data()
            self.clear_form()

    # --- Logic: "Mark as Returned" Button ---
    def mark_as_returned(self):
        current_row = self.table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Select Item", "Please select an item first.")
            return

        if not self.check_permission(current_row):
            QMessageBox.critical(self, "Denied", "You can only update your own posts.")
            return

        # Check if it's already done
        current_status = self.table.item(current_row, 1).text()
        if current_status == "Returned":
            QMessageBox.information(self, "Info", "This item is already marked as returned.")
            return

        # Confirmation Popup
        reply = QMessageBox.question(
            self, 'Confirm Return', 
            'Has this item been found/returned?\nThis will mark the case as closed.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            item_id = self.table.item(current_row, 0).text()
            # Force status to "Returned"
            self.db.update_item(
                item_id, 
                self.name_input.text(), 
                self.desc_input.toPlainText(), 
                "Returned",  
                self.contact_input.text(),
                self.current_image_path
            )
            self.load_data()
            self.clear_form()
            QMessageBox.information(self, "Success", "Item marked as Returned!")

    # --- Logic: "Delete Post" Button ---
    def delete_item(self):
        current_row = self.table.currentRow()
        if current_row < 0: return

        if not self.check_permission(current_row):
            QMessageBox.critical(self, "Denied", "You can only delete your own posts.")
            return

        # Confirmation Popup
        reply = QMessageBox.question(
            self, 'Confirm Delete', 
            'Are you sure you want to delete this post?\n\nThis cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            item_id = self.table.item(current_row, 0).text()
            self.db.delete_item(item_id)
            self.load_data()
            self.clear_form()

    # --- Logic: "Clear Form" Button & Automatic Reset ---
    def clear_form(self):
        self.name_input.clear()
        self.desc_input.clear()
        self.contact_input.clear()
        self.current_image_path = ""
        self.image_preview.clear()
        self.image_preview.setText("No Image Selected")
        self.table.clearSelection()