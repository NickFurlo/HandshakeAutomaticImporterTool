# Handshake Automatic Importer by Nick Furlo 5/17/18
# TODO Error handle for finding elements
import configparser
import os
import time
import tkinter
from datetime import datetime
from pathlib import Path
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askopenfilename

from selenium import webdriver
from selenium.webdriver.support.ui import Select


# Creates config files if there is none. Loads values from config files into variables.
def load_config():
    # If there is no config file, make one.
    config = configparser.ConfigParser()
    my_file = Path("Importer.config")
    if not my_file.is_file():
        file = open("Importer.config", "w+")
        file.write(
            "[DEFAULT]\nUSERNAME = \nCSV_FILE_PATH = \nNEW_JOB_DESCRIPTION = ""New upload from Database. Job created "
            "by automatic importer python script"" \nFAILED_ROWS_DESCRIPTION = ""Upload of fixed rows. Job created by "
            "automatic importer python script.\n""USE_ALT_DATE_FORMAT = \nTEST_JOB = ")
        messagebox.showinfo("Warning", "Config file created. Please add a CSV file path and relaunch the program.")
        driver.close()
        sys.exit()

    # Read config and set variables
    config.read('Importer.config')
    global file_path, failed_description, new_description, alt_date, test_job, username

    username = config['DEFAULT']['USERNAME']
    file_path = config['DEFAULT']['CSV_FILE_PATH']
    new_description = config['DEFAULT']['NEW_JOB_DESCRIPTION']
    failed_description = config['DEFAULT']['FAILED_ROWS_DESCRIPTION']
    alt_date_str = config['DEFAULT']['USE_ALT_DATE_FORMAT']
    test_job_str = config['DEFAULT']['TEST_JOB']

    if alt_date_str in ['yes', 'Yes', 'YES', 'True', 'true', 'TRUE']:
        alt_date = True
    else:
        alt_date = False

    if test_job_str in ['yes', 'Yes', 'YES', 'True', 'true', 'TRUE']:
        test_job = True
    else:
        test_job = False

    if file_path is "":
        messagebox.showinfo("Warning", "Please enter a CSV file path into the config file and relaunch the program.")
        driver.close()
        sys.exit()


# Checks to make sure the CSV was made today.
# Return true if CSV was made today
def check_csv():
    unix_time = os.path.getmtime(file_path)
    date_created = datetime.fromtimestamp(unix_time).strftime('%Y-%m-%d')
    today = time.strftime('%Y-%m-%d')
    if today == date_created:
        return True
    else:
        messagebox.showinfo("Error", "The CSV is more than a day old! Date created: " + date_created)
        return False


# Startup main menu GUI
def main_menu():
    root = tkinter.Tk()
    root.title("Auto Importer")
    root.minsize(475, 100)
    root.iconbitmap('updown.ico')


    Label(master=root, text="Welcome to the Handshake Automatic Importer").grid(row=0, column=2)
    Label(master=root, text=" ").grid(row=1, column=2)

    # Create buttons.
    button1 = tkinter.Button(master=root, text='Upload New CSV', command=lambda: upload_csv(False, root), height=2,
                             width=18)
    button2 = tkinter.Button(master=root, text='Download Failed Rows', command=lambda: download_failed_rows(root),
                             height=2, width=18)
    button3 = tkinter.Button(master=root, text='Upload Fixed Failed Rows', command=lambda: upload_csv(True, root),
                             height=2, width=18)
    button1.grid(row=3, column=1)
    button2.grid(row=3, column=2)
    button3.grid(row=3, column=3)

    root.mainloop()


# Waits for user to fill in login form
def login():
    if len(username) > 0:
        driver.find_element_by_id('user_email').send_keys(username)
    while "Log in" in driver.page_source:
        time.sleep(1)
    if "Signed in successfully." in driver.page_source:
        return


# Uploads csv file to importer. If set_identifier is true, uploading failed rows.
def upload_csv(set_identifier, root):
    global file_path
    global driver
    # Open importer
    root.destroy()
    driver.get('https://importer.joinhandshake.com/')
    login()

    # New gui
    root2 = tkinter.Tk()
    root2.title("Upload CSV")
    root2.iconbitmap('updown.ico')

    root2.withdraw()

    # Open CSV Upload
    driver.find_element_by_partial_link_text("Upload New CSV").click()

    # gets file path from user if uploading failed rows. Otherwise grabs CSV from handshake.
    if set_identifier:
        file_path = askopenfilename()
        root2.update()

    # check for correct page
    assert "Upload new CSV" in driver.page_source

    # Check if CSV is new
    if not set_identifier and not check_csv():
        return

    # Upload file to page and fill out form.
    file_button = driver.find_element_by_name("job[file]")
    file_button.send_keys(file_path)

    # Select students from drop down menu
    job_type = Select(driver.find_element_by_name('job[job_type]'))
    job_type.select_by_value("users")

    # Type description and show GUI messagebox's to ask user if change identifier data should be checked in the
    # handshake importer. # return true if identifier should be changed.
    description = driver.find_element_by_name("job[description]")
    if set_identifier:
        result = messagebox.askquestion("Job Type", "Are you sure you wish to change identifier data?", icon='warning')
        if result == 'yes':
            driver.find_element_by_xpath('//*[@id="new_job"]/div[6]/div/label/div').click()
            #                             //*[@id="new_job"]/div[6]/div/label
            description.send_keys(failed_description)
    else:
        description.send_keys(new_description)

    if alt_date:
        driver.find_element_by_xpath('//*[@id="new_job"]/div[5]/div/label/div').click()
    if test_job:
        driver.find_element_by_xpath('//*[@id="new_job"]/div[4]/div/label/div[2]').click()

    root2.update()
    # Click "Save Job"
    driver.find_element_by_name("button").click()

    main_menu()


# Finds and returns job number on web page
def find_job_number():
    if "Users import for Oakland University" in driver.page_source:
        return int(driver.find_element_by_xpath("/html/body/div[1]/div/div/h2").text[1:6])
    else:
        return 0


# Query uer for job number Navigate to job page and download failed rows.
def download_failed_rows(root):
    # Open job page and download failed rows CSV
    def pull_file():
        global job_number
        if job_number is None or int(job_number) < 63731 or int(job_number) > 99999:
            print("job_number: " + str(job_number))
            set_job_number()
        root2.destroy()
        # Open Google Chrome
        driver.get("https://importer.joinhandshake.com")
        login()
        driver.get("https://importer.joinhandshake.com/jobs/" + str(job_number))
        driver.get("https://importer.joinhandshake.com/jobs/" + str(job_number) + "/download_failed_file")

    # Set's the job_number with text input from the user. Only executed after "Submit" is clicked.
    def set_job_number():
        global job_number
        job_number = float(job_number)
        if float(e1.get()) < 63731 or float(e1.get()) > 99999:
            messagebox.showerror("Error", "Pleas enter a valid job number.", icon='error')
            return
        job_number = int(e1.get())
        global job_number_set
        job_number_set = True
        pull_file()
        return

    # Close main menu, open new gui.
    root.destroy()
    root2 = tkinter.Tk()
    root2.iconbitmap('updown.ico')
    global job_number_set

    # Try and grab job number from web page
    job_number = find_job_number()
    if 63731 < int(job_number) < 99999:
        job_number_set = True

    # Open text box if job_number is not set, otherwise double check value with user and pull_file().
    if not job_number_set:
        Label(root2, text="Job Number").grid(row=0)

        e1 = Entry(root2)
        button1 = tkinter.Button(master=root2, text='submit', command=lambda: set_job_number(), height=2,
                                 width=5)
        e1.grid(row=0, column=1)
        button1.grid(row=0, column=2)
    else:
        job_number_set = messagebox.askquestion("Job Number", "Is " + str(job_number) + " the correct job number?")
        pull_file()
    main_menu()


# Connect to chrome instance
driver = webdriver.Chrome()

# Startup GUI and initialise variables
job_number_set = False
job_number = 0
username = ""
file_path = ""
new_description = ""
failed_description = ""
alt_date = False
test_job = False
load_config()
main_menu()
