# This file should not contain hardcoded secrets.
# Use environment variables and secure password management instead.
import streamlit_authenticator as stauth

hasher = stauth.Hasher(['rrou qocy zmff naiee'])
hashed_passwords = hasher.generate()
print(hashed_passwords[0])