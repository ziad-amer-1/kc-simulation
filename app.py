from flask import Flask, request, render_template, jsonify, redirect, url_for
import requests
import openpyxl
from selenium import webdriver
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import tkinter as tk
# from selenium.webdriver.firefox.firefox_binary import FirefoxBinary


app = Flask(__name__, template_folder="view")


KEYCLOAK_URL = 'http://localhost:1111'
REALM_NAME = 'FIDO'
TOKEN_ENDPOINT = f'{KEYCLOAK_URL}/realms/master/protocol/openid-connect/token'
USER_ACCOUNT_ENDPOINT = f'{KEYCLOAK_URL}/realms/{REALM_NAME}/account'
CREATE_USER_ENDPOINT = f'{KEYCLOAK_URL}/admin/realms/{REALM_NAME}/users'
CLIENT_ID = 'admin-cli'
GRANT_TYPE = 'password'
USERNAME = 'ziad'
PASSWORD = 'ziadamerZz1'
root = tk.Tk()
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.destroy()
kc_window_width = 500
kc_window_height = 700
x_position = (screen_width - kc_window_width) // 2
y_position = (screen_height - kc_window_height) // 2

# print(f'''
#     screen_width = {screen_width}
#     screen_height = {screen_height}
#     window_width = {kc_window_width}
#     window_height = {kc_window_height}
#     x_position = {x_position}
#     y_position = {y_position}
# ''')

TOKEN_DATA = {
    'grant_type': GRANT_TYPE,
    'client_id': CLIENT_ID,
    'username': USERNAME,
    'password': PASSWORD
}

def get_token():
    token_request = requests.post(TOKEN_ENDPOINT, data=TOKEN_DATA)
    return token_request.json().get('access_token')

def open_chrome(username):
    try:

        # binary = FirefoxBinary('path/to/binary')

        # options = webdriver.FirefoxOptions()
        # options._binary = binary

        # chrome_options = webdriver.ChromeOptions()
        # chrome_options.add_argument(f'--window-size={kc_window_width},{kc_window_height}')
        # chrome_options.add_argument(f'--window-position={x_position},{y_position}')


        browser = webdriver.Chrome()

        browser.minimize_window()

        browser.get(USER_ACCOUNT_ENDPOINT)

        wait = WebDriverWait(browser, 15)

        singInButton = wait.until(EC.element_to_be_clickable((By.ID, "landingSignInButton")))

        singInButton.click()

        loginButton = wait.until(EC.presence_of_element_located((By.ID, 'kc-login')))

        usernameInput = browser.find_element(By.ID, 'username')

        usernameInput.send_keys(username)

        loginButton.click()

        singInWithSecurityKeyButton = wait.until(EC.presence_of_element_located((By.ID, 'authenticateWebAuthnButton')))

        singInWithSecurityKeyButton.click()

        
        # browser.maximize_window()

        browser.set_window_size(kc_window_width, kc_window_height)
        browser.set_window_position(x_position, y_position)

        logoutButton = wait.until(EC.presence_of_element_located((By.ID, 'landingSignOutButton')))
        currentLoginUserName = wait.until(EC.presence_of_element_located((By.ID, 'landingLoggedInUser')))

        print("button " + logoutButton.get_attribute("innerHTML"))
        print("username " + currentLoginUserName.get_attribute("innerHTML"))

        loginInnerHTML = logoutButton.get_attribute("innerHTML")

        browser.close()

        if loginInnerHTML == 'Sign out':
            return jsonify({'status': 'true'})
        return jsonify({'status': 'false'})
    except Exception as e:
        print("err: " + e.__str__())
        return jsonify({'status': 'false'})

@app.route('/', methods=["GET"])
def index():
    return render_template('upload.html')


@app.route('/upload', methods=['POST'])
def upload():

    token = get_token()

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    print(token)

    uploaded_file = request.files['file']
    if uploaded_file.filename != '':
        wb = openpyxl.load_workbook(uploaded_file)
        sheet = wb.active
        for row in sheet.iter_rows(min_row=2, values_only=True):
            user = {
                "enabled": True,
                "firstName": row[0],
                "lastName": row[1],
                "username": str(row[0]) + " " + str(row[1]),
                "groups": [],
                "attributes": {
                    "id": row[2],
                    "startDate":str(row[3]),
                    "endDate":	str(row[4]),
                    "regionalCenter":row[5],
                    "government" :row[6],
                    "operationId": row[7]
                }
            }
            r = None
            try:
                r = requests.post(CREATE_USER_ENDPOINT, headers=headers, json=user)
            except Exception as e:
                print(str(jsonify({
                'message': f"error occurred while creating user with username = {str(row[0])} {str(row[1])}",
                'description': e.__str__(),
                'status_code': str(r.status_code)
            })))
        

        # return render_template('success.html')
        # return redirect(url_for('view', index='success.html'))
        return jsonify({'message': 'done '})
    # return render_template('error.html')
    return jsonify({'message': 'error happen while trying to add users'})


# @app.route('/success', methods=['GET'])
# def success_page():
#     return render_template('success.html')

@app.route('/login', methods=['GET'])
def login():
    usernmae = str(request.args.get("username"))
    print(usernmae)
    return open_chrome(usernmae)

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0")
