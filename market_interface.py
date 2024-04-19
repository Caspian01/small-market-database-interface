import time
from tkinter import messagebox
import customtkinter
from PIL import Image, ImageTk
import sqlite3
from datetime import datetime

def login(user_id_input, password_input, error_label, login_frame):
    global current_user
    username_id = user_id_input.get()
    password = password_input.get()

    if username_id in username_password_dict.keys() and password == username_password_dict[username_id]:
        print('Correct')

        cursor.execute(f'SELECT* FROM Users WHERE Email = "{username_id}"')
        user_list = cursor.fetchall()[0]

        current_user = user_list[0]
        login_frame.destroy()
        initiate_main_login_window(user_list)
    else:
        error_label.configure(text='The data provided is incorrect. Please try again.')
        user_id_input.delete(0, customtkinter.END)
        password_input.delete(0, customtkinter.END)

def find_center_screen(width_login_window, height_login_window):

    x_middle = int((root.winfo_screenwidth() - width_login_window) / 2)
    y_middle = int((root.winfo_screenheight() - height_login_window) / 2)

    return x_middle, y_middle

def item_search(search_item_entry, label_search_result):

    print(search_item_entry)

    label_search_result.configure(text='')
    
    # Fetching all data for that item and department info
    try:
        cursor.execute(f'SELECT * FROM Items INNER JOIN Departments ON Items.DepartmentID = Departments.DepartmentID WHERE Items.ItemID = "{search_item_entry}" OR Items.Description = "{search_item_entry}"')

        item_info = cursor.fetchall()[0]

        message_output = f"""
        'ItemID: {item_info[0]}'\n\n'Product Description/Name: {item_info[1]}'\n\n'Price: ${item_info[2]}'\n\n'Expiration Date: {item_info[3]}'\n\n'Amount Left in Store: {item_info[4]}'\n\n'Department Located: {item_info[7]}'\n\n'Department Description: {item_info[8]}'
        """

        message_output = message_output.replace("'", "").strip()

        #Displaying data fetched
        label_search_result.configure(text=message_output)
    except IndexError:
        label_search_result.configure(text=f'The item you tried to seach is not in store')
    except UnboundLocalError:
        pass

def add_to_cart(entry_cart, cart_display_info):

    entry_cart_text = entry_cart.get()

    if entry_cart_text in list(itemid_name_dict.keys()):
        cursor.execute(f'SELECT * FROM Items WHERE ItemID = "{entry_cart_text}" OR Description = "{entry_cart_text}"')

        item_info = cursor.fetchall()[0]

        product_name_char = len(str(item_info[1]))
        product_price_char = len(str(item_info[2]))

        char_difference = 100 - (product_name_char + product_price_char)
        char_difference = '.'*char_difference

        message_ouput = f"{item_info[1]}{char_difference}{item_info[2]}"

        product_display = customtkinter.CTkLabel(cart_display_info, text=message_ouput, wraplength=450, justify="left")
        product_display.grid(column=0, sticky='nw')

        list_cart_items.append(entry_cart_text)
    else:
        messagebox.showinfo("Alert", f"There are no items with an ID of: {entry_cart_text}. Please try again")
        entry_cart.delete(0, customtkinter.END)

def test_for_existance(amount_of_each_item):
    database_item_count = []
    lacking_items = []
    list_of_keys_items_in_cart = list(amount_of_each_item.keys())

    for item_id in list_of_keys_items_in_cart:
        cursor.execute("SELECT StockAmount FROM Items WHERE ItemID = ?", (item_id,))
        database_item_count.append(int(cursor.fetchone()[0]))

    for item_amount in range(len(database_item_count)):
        if database_item_count[item_amount] < amount_of_each_item[list_of_keys_items_in_cart[item_amount]]:
            lacking_items.append(list_of_keys_items_in_cart[item_amount])

    return lacking_items
        

def process_payment(entry_customer_first_name, entry_customer_last_name, entry_card_number, tab_view):
    local_cart_items = list_cart_items

    amount_of_each_item = {}

    for item in local_cart_items:
        if item in amount_of_each_item:
            amount_of_each_item[item] += 1
        else:
            amount_of_each_item[item] = 1

    lacking_items = test_for_existance(amount_of_each_item)

    if len(lacking_items) == 0 and len(local_cart_items) != 0:
        cust_first_name = entry_customer_first_name.get()
        cust_customer_last_name = entry_customer_last_name.get()
        cust_card_number = entry_card_number.get()

        cursor.execute("SELECT MAX(CustomerID) FROM Customer")
        customer_id = int(cursor.fetchone()[0]) + 1

        customer_data = (customer_id, cust_first_name, cust_customer_last_name, cust_card_number)

        # Inserting into database Customer Info
        cursor.execute("INSERT INTO Customer (CustomerID, FirstName, LastName, PaymentCard) VALUES (?, ?, ?, ?)", customer_data)
        connect.commit()

        # Inserting Info into TransactionID & Updating Items Amount in Store
        for item_id in local_cart_items:
            cursor.execute("SELECT Price FROM Items WHERE ItemID = ?", (item_id,))
            result = cursor.fetchone()
            final_amount_charged = float(result[0]) + (float(result[0]) * 0.06)
            final_amount_charged = round(final_amount_charged, 2)

            date = datetime.now().date()

            transaction_record_data = (item_id, final_amount_charged, customer_id, current_user, date, 0.06)

            cursor.execute("INSERT INTO TransactionRecord (ItemID, FinalAmountCharged, CustomerID, UsersID, Date, SalesTaxRate) VALUES (?, ?, ?, ?, ?, ?)", transaction_record_data)
            connect.commit()

            cursor.execute("SELECT StockAmount FROM Items WHERE ItemID = ?", (item_id,))
            initial_amount = cursor.fetchone()
            updated_amount = int(initial_amount[0]) - 1

            cursor.execute("UPDATE Items SET StockAmount = ? WHERE ItemID = ?", (updated_amount, item_id))
            connect.commit()

        messagebox.showinfo("Alert", f"Congrats! Your transaction has been successfully processed.")

        tab_view.delete("Cart")
        create_cart_tab(tab_view)
    else:
        messagebox.showinfo("Alert", f"There has been an error. Your cart is empty or there might be not enough of the following items to complete this transaction: {[itemid_name_dict[key] for key in lacking_items]}")

        tab_view.delete("Cart")
        create_cart_tab(tab_view)

        local_cart_items.clear()
        amount_of_each_item.clear()
        lacking_items.clear()

def get_new_user_info_and_store(label_add_new_user, new_user_list):

    cursor.execute('SELECT Email FROM Users')
    data = [item[0] for item in cursor.fetchall()]
    print(len(new_user_list[2].get()))

    if new_user_list[2].get() in data or len(new_user_list[2].get()) == 0:
        label_add_new_user.configure(text="The Email you provided is already assigned to one of our Users or you forgot to provide an Email")
    else:
        cursor.execute('SELECT * FROM Users')
        data = cursor.fetchall()
        number_users = len(data) + 1

        temp_new_user_list = [element.get() for element in new_user_list]
        temp_new_user_list.insert(0, number_users)

        cursor.execute("INSERT INTO Users (UsersID, FirstName, LastName, Email, Admin, Password) VALUES (?, ?, ?, ?, ?, ?)", temp_new_user_list)
        connect.commit()

    for element in new_user_list:
        try:
            element.delete(0, customtkinter.END)
        except AttributeError:
            pass

def sql_script(sql_textbox, label_query_result):
    query = sql_textbox.get("0.0", "end")
    query = query.replace(";", "").strip()

    cursor.execute(query)

    data = cursor.fetchall()

    output_list = []

    for data_tuple in data:
        for element in data_tuple:
            output_list.append(str(element))
        output_list.append("============")

    output_message = '\n'.join(output_list)

    label_query_result.configure(text=output_message)

def create_cart_tab(tab_view):
    tab_view.add("Cart")

    label_customer_info = customtkinter.CTkLabel(master=tab_view.tab("Cart"), text="Customer Info", justify="center", width=215)
    label_customer_info.pack(padx=15, expand=False, anchor='nw')

    customer_info_frame = customtkinter.CTkFrame(master=tab_view.tab("Cart"), fg_color="#4a4a4a", border_color="#e3f3fa", border_width=2, width=215, height=450)
    customer_info_frame.pack(padx=10, pady=2, anchor='nw')

    label_customer_first_name = customtkinter.CTkLabel(customer_info_frame, text='Customer First Name', width=215, wraplength=200, justify="left")
    label_customer_first_name.pack(padx=5, pady=5, anchor='nw')

    entry_customer_first_name = customtkinter.CTkEntry(customer_info_frame, justify="center")
    entry_customer_first_name.pack(padx=5, pady=5)

    label_customer_last_name = customtkinter.CTkLabel(customer_info_frame, text='Customer Last Name', width=215, wraplength=200, justify="left")
    label_customer_last_name.pack(padx=5, pady=5, anchor='nw')

    entry_customer_last_name = customtkinter.CTkEntry(customer_info_frame, justify="center")
    entry_customer_last_name.pack(padx=5, pady=5)

    label_card_number = customtkinter.CTkLabel(customer_info_frame, text='Customer Card Number', width=215, wraplength=200, justify="left")
    label_card_number.pack(padx=5, pady=5, anchor='nw')

    entry_card_number = customtkinter.CTkEntry(customer_info_frame, justify="center")
    entry_card_number.pack(padx=5, pady=5)

    label_cart_error_message = customtkinter.CTkLabel(master=tab_view.tab("Cart"), text="", justify="center", width=215, wraplength=200)
    label_cart_error_message.pack(padx=15, expand=False, anchor='nw')

    search_item_button = customtkinter.CTkButton(customer_info_frame, text='Process Payment', width=200, command=lambda: process_payment(entry_customer_first_name, entry_customer_last_name, entry_card_number, tab_view))
    search_item_button.pack(padx=10, pady=10)

    # Cart
    cart_label = customtkinter.CTkLabel(master=tab_view.tab("Cart"), text='Cart by ItemID', width=450, justify="center")
    cart_label.place(x=300, y=5)

    cart_display_info = customtkinter.CTkScrollableFrame(master=tab_view.tab("Cart"), fg_color="#4a4a4a", border_color="#e3f3fa", border_width=2, width=450, height=285)
    cart_display_info.place(x=300, y=30)

    entry_cart = customtkinter.CTkEntry(master=tab_view.tab("Cart"), width=475, justify="center")
    entry_cart.place(x=300, y=340)

    add_item_cart_button = customtkinter.CTkButton(master=tab_view.tab("Cart"), text='Add to Cart',command=lambda: add_to_cart(entry_cart, cart_display_info), width=475)
    add_item_cart_button.place(x=300, y=375)

def initiate_main_login_window(users_list):
    width_login_window = 800
    height_login_window = 600
    x_center, y_center = find_center_screen(width_login_window, height_login_window)
    root.geometry(f'{width_login_window}x{height_login_window}+{x_center}+{y_center}')

    tab_view = customtkinter.CTkTabview(root)
    tab_view.pack(fill='both', expand=True)

    tab_view.add("User")
    tab_view.add("Search")

    # User Info tab
    user_frame = customtkinter.CTkFrame(master=tab_view.tab("User"), fg_color="#4a4a4a", border_color="#e3f3fa", border_width=2, width=200, height=300)
    user_frame.pack(padx=10, pady=10, expand=False, anchor='nw')

    list_user_local = users_list

    user_id_label = customtkinter.CTkLabel(user_frame, text=f'User ID: {list_user_local[0]}', width=215, wraplength=200)
    user_id_label.pack(anchor="nw", expand=True, pady=2, padx=6)

    user_full_name_label = customtkinter.CTkLabel(user_frame, text=f'Full Name: {list_user_local[1]} {list_user_local[2]}', width=215, wraplength=200)
    user_full_name_label.pack(anchor="nw", expand=True, pady=2, padx=6)

    user_email_id_label = customtkinter.CTkLabel(user_frame, text=f'Email: {list_user_local[3]}', width=215, wraplength=200)
    user_email_id_label.pack(anchor="nw", expand=True, pady=2, padx=6)

    user_admin_status_label = customtkinter.CTkLabel(user_frame, text=f'Admin: {"Yes" if list_user_local[4] == 1 else "No"}', width=215, wraplength=200)
    user_admin_status_label.pack(anchor="nw", expand=True, pady=2, padx=6)

    #Special Privileges for Admin
    if list_user_local[4] == 1:
        add_user_frame = customtkinter.CTkFrame(master=tab_view.tab("User"), fg_color="#4a4a4a", border_color="#e3f3fa", border_width=2, width=300, height=300)
        add_user_frame.pack(padx=10, pady=5, expand=False, anchor='nw')

        label_add_new_user = customtkinter.CTkLabel(add_user_frame, text='Follow instructions to add a new User.', wraplength=200, width=207)
        label_add_new_user.pack(padx=10, pady=10, expand=False)

        ask_first_name = customtkinter.CTkLabel(add_user_frame, text='First Name')
        ask_first_name.pack(padx=10, pady=3, expand=False)
        entry_first_name = customtkinter.CTkEntry(add_user_frame)
        entry_first_name.pack(padx=10, pady=2, expand=False)

        ask_last_name = customtkinter.CTkLabel(add_user_frame, text='Last Name')
        ask_last_name.pack(padx=10, pady=3, expand=False)
        entry_last_name = customtkinter.CTkEntry(add_user_frame)
        entry_last_name.pack(padx=10, pady=2, expand=False)

        ask_email_address = customtkinter.CTkLabel(add_user_frame, text='Email Address')
        ask_email_address.pack(padx=10, pady=3, expand=False)
        entry_email_address = customtkinter.CTkEntry(add_user_frame)
        entry_email_address.pack(padx=10, pady=2, expand=False)

        ask_password = customtkinter.CTkLabel(add_user_frame, text='Password')
        ask_password.pack(padx=10, pady=3, expand=False)
        entry_password = customtkinter.CTkEntry(add_user_frame)
        entry_password.pack(padx=10, pady=2, expand=False)
        
        switch_is_admin = customtkinter.CTkSwitch(add_user_frame, text='Admin', onvalue=1, offvalue=0)
        switch_is_admin.pack(padx=10, pady=3, expand=False)

        add_user_button = customtkinter.CTkButton(add_user_frame, text='Add User', command=lambda: get_new_user_info_and_store(label_add_new_user, [entry_first_name, entry_last_name, entry_email_address, switch_is_admin, entry_password]))
        add_user_button.pack(padx=10, pady=5, expand=False)

        # TextBox for Direct SQL
        label_sql_instructions = customtkinter.CTkLabel(master=tab_view.tab("User"), text='You may write SQL queries in the textbox below and interact with the database directly.')
        label_sql_instructions.place(x=300, y=5)

        # Write SQL
        sql_textbox = customtkinter.CTkTextbox(master=tab_view.tab("User"), scrollbar_button_color="white", border_width=2, fg_color="#4a4a4a", border_color="#e3f3fa", width=475, height=200)
        sql_textbox.place(x=300, y=30)

        #Visualize Query
        query_result_frame = customtkinter.CTkScrollableFrame(master=tab_view.tab("User"), fg_color="#4a4a4a", border_color="#e3f3fa", orientation="vertical",  border_width=2, width=450, height=50)
        query_result_frame.place(x=300, y=240)

        label_query_result = customtkinter.CTkLabel(query_result_frame, text='', wraplength=200, width=400, height=50)
        label_query_result.pack(padx=10, pady=10, expand=False, anchor='nw')

        run_query_button = customtkinter.CTkButton(master=tab_view.tab("User"), text='Run SQL', command=lambda: sql_script(sql_textbox, label_query_result), width=475)
        run_query_button.place(x=300, y=470)

    # Product Search tab
    label_product_options_info = customtkinter.CTkLabel(master=tab_view.tab("Search"), text="List of IDs - Product Descriptions", justify="center", width=200)
    label_product_options_info.pack(padx=15, expand=False, anchor='nw')

    product_options_frame = customtkinter.CTkScrollableFrame(master=tab_view.tab("Search"), fg_color="#4a4a4a", border_color="#e3f3fa", orientation="vertical",  border_width=2, width=200, height=500)
    product_options_frame.pack(padx=10, pady=2, anchor='nw')

    itemid_name_dict_output = "\n".join(f"{key} - {value}\n" for key, value in itemid_name_dict.items())

    label_product_options = customtkinter.CTkLabel(product_options_frame, text=itemid_name_dict_output, wraplength=200, width=180, justify="left", height=450)
    label_product_options.pack(padx=10, pady=10, expand=False, anchor='nw')

    label_sql_instructions = customtkinter.CTkLabel(master=tab_view.tab("Search"), text='Search by ID', width=450, justify="center")
    label_sql_instructions.place(x=300, y=5)

    display_product_info = customtkinter.CTkScrollableFrame(master=tab_view.tab("Search"), fg_color="#4a4a4a", border_color="#e3f3fa", border_width=2, width=450, height=285)
    display_product_info.place(x=300, y=30)

    label_search_result = customtkinter.CTkLabel(display_product_info, text='', width=475, height=210, wraplength=450, justify="left")
    label_search_result.pack(padx=5, pady=5, anchor='nw')

    entry_itemid_or_name = customtkinter.CTkEntry(master=tab_view.tab("Search"), width=475, justify="center")
    entry_itemid_or_name.place(x=300, y=340)

    search_item_button = customtkinter.CTkButton(master=tab_view.tab("Search"), text='Search',command=lambda: item_search(entry_itemid_or_name.get(), label_search_result), width=475)
    search_item_button.place(x=300, y=375)

    # Cart tab
    create_cart_tab(tab_view)

def login_window():
    # Provide window dimentions
    width_login_window = 300
    height_login_window = 300
    x_center, y_center = find_center_screen(width_login_window, height_login_window)

    root.geometry(f'{width_login_window}x{height_login_window}+{x_center}+{y_center}')
    root.title('Log In')

    login_frame = customtkinter.CTkFrame(root, height=200)
    login_frame.pack(fill='both', expand=True)

    # Welcoming message
    username_label = customtkinter.CTkLabel(login_frame, text="Welcome to the Market Operations System", font=("League Spartan", 25), wraplength=300)
    username_label.pack(pady=20)

    # Creating labels and entries for username and password
    widget_font = ('League Spartan', 15)

    user_id_label = customtkinter.CTkLabel(login_frame, text="User ID", font=widget_font).pack()
    user_id_input = customtkinter.CTkEntry(login_frame)
    user_id_input.pack()

    password_label = customtkinter.CTkLabel(login_frame, text="Password", font=widget_font)
    password_label.pack()
    password_input = customtkinter.CTkEntry(login_frame, show='*')
    password_input.pack()

    error_label = customtkinter.CTkLabel(login_frame, text='', font=('League Spartan', 12))
    error_label.pack()

    # Log in Button
    login_button = customtkinter.CTkButton(login_frame, text='Log In', command=lambda: login(user_id_input, password_input, error_label, login_frame))
    login_button.pack() 

# Creating a dictionary so it can be used for Log In window
def dictionary_users():
    cursor.execute('SELECT * FROM Users')

    data_users = cursor.fetchall()

    return {row[3]: row[5] for row in data_users}

def dictionary_items():
    cursor.execute('SELECT * FROM Items')

    data_items = cursor.fetchall()

    return {row[0]: row[1] for row in data_items}


if __name__ == "__main__":
    connect = sqlite3.connect('market_database.db')
    cursor = connect.cursor()

    # Fetching email and password
    username_password_dict = dictionary_users()
    print(username_password_dict)

    # Fetching Item ID and Name
    itemid_name_dict = dictionary_items()
    
    # List of items in cart
    list_cart_items = []

    # ID of current User
    current_user = int()

    root = customtkinter.CTk()
    root.resizable(False, False)

    customtkinter.set_appearance_mode('dark')
    customtkinter.set_default_color_theme('dark-blue')

    login_window()
    
    root.mainloop()
    connect.close()