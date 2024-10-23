import dotenv
import os

def generate_jwt(client):

    # dotenv.load_dotenv()

    # testUser = os.getenv("LOGIN_USERNAME")
    # testPassword = os.getenv("LOGIN_PASSWORD")

    # data = {
    #     'Content-Type': 'application/json',
    #     'username': testUser,
    #     'password': testPassword
    # }

    # response = client.post("/api/v1/login", json=data)
    # access_token = response.json["access_token"]

    # headers = {
    #     "Authorization": f"Bearer {access_token}"
    # }

    #temp fix
    headers = {
        "Authorization": "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjI5MDMyMzA4MjA1NTMxOTA1OSIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJodHRwczovL3ppdGFkZWwuZGF0YWJlbmRpbmcuY2EiLCJzdWIiOiIyODgwMzQwNjE1ODUyODQ2MjciLCJhdWQiOlsiMjg3MjcyNTExOTkxODQwMjc1IiwiMjg4Mjk2MzI2MDQ1NzYxMDQzIiwiMjg3MjcyMzUzMjk2MDg4NTk1Il0sImV4cCI6MTcyOTU4NTI0MiwiaWF0IjoxNzI5NTQyMDQyLCJhdXRoX3RpbWUiOjE3Mjk1NDIwMzcsImFtciI6WyJwd2QiXSwiYXpwIjoiMjg3MjcyNTExOTkxODQwMjc1IiwiY2xpZW50X2lkIjoiMjg3MjcyNTExOTkxODQwMjc1IiwiYXRfaGFzaCI6InRWOFVEZDM4X2VJT1gwREwtTzRFYmciLCJzaWQiOiJWMV8yOTAzMjMwNzUxMDk1NTE2MzUiLCJuYW1lIjoiVGVzdCBDYXBzdG9uZSIsImdpdmVuX25hbWUiOiJUZXN0IiwiZmFtaWx5X25hbWUiOiJDYXBzdG9uZSIsImxvY2FsZSI6bnVsbCwidXBkYXRlZF9hdCI6MTcyODE3NzY4MCwicHJlZmVycmVkX3VzZXJuYW1lIjoiVGVzdENhcHN0b25lIiwiZW1haWwiOiJ0ZXN0QGRhdGFiZW5kaW5nLmNhIiwiZW1haWxfdmVyaWZpZWQiOnRydWV9.ji1BQ66y7ORLO59gAFOlCmIT9HiAgegn8i3mvl3uD2LijMILcoahwRuGrZU62XfJ0ziOxkUaNxeqNNk7Ha7lsq0xQrcnOGwuICx4onBSAOht3gK90IVf0Bl4xePGrkaYmD_3bcx041hLNh1jN01q-R9HIUiDoJ12bolqKxLNXxukUWQOlg4p7x0o0g5es7VodJ2K7pIkDw-BWAOI1aWovNp88qwtt4o3GgpBspI5VNO9Bm9jewM-D1ZOA8Tq7O_NcYtzTzEzuQj2nE0Kkk4Htou1smssA-43T-D1Ltn9PTR3RflQ3TD790eyxT0q2ERMHFNM3jysMyGWdSOfpWdfSQ"
    }

    return headers
