import jwt
from jwt.exceptions import PyJWTError  as JWTError  # If you're using PyJWT
from datetime import datetime, timedelta

class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.ACCESS_TOKEN_EXPIRE_TIME = timedelta(days=7)  # Access token expires in 7 days
        self.REFRESH_TOKEN_EXPIRE_TIME = timedelta(days=21)  # Refresh token expires in 21 days

    # Create an access token
    def create_access_token(self, data: dict, expires_delta: timedelta = None):
        expires_delta = expires_delta or self.ACCESS_TOKEN_EXPIRE_TIME
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    # Create a refresh token
    def create_refresh_token(self, data: dict, expires_delta: timedelta = None):
        expires_delta = expires_delta or self.REFRESH_TOKEN_EXPIRE_TIME
        to_encode = data.copy()
        expire = datetime.utcnow() + expires_delta
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    # Verify and decode the JWT token
    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise Exception("Token has expired")
        except JWTError:
            raise Exception("Invalid token")

    # Refresh the access token using the refresh token
    def refresh_access_token(self, refresh_token: str):
        try:
            # Decode the refresh token
            payload = jwt.decode(refresh_token, self.secret_key, algorithms=[self.algorithm])
            
            # Generate new access token using the information from the refresh token payload
            new_access_token = self.create_access_token(data={"sub": payload["sub"]})
            return new_access_token
        
        except jwt.ExpiredSignatureError:
            raise Exception("Refresh token has expired")
        except JWTError:
            raise Exception("Invalid refresh token")


# Example usage
# if __name__ == "__main__":
#     jwt_manager = JWTManager(secret_key="your_secret_key")

#     data = {"sub": "user@example.com"}  # User's identifier, usually email or user ID

#     # Create access token and refresh token
#     access_token = jwt_manager.create_access_token(data)
#     refresh_token = jwt_manager.create_refresh_token(data)

#     print("Generated Access Token:", access_token)
#     print("Generated Refresh Token:", refresh_token)

#     # Verifying the access token
#     try:
#         decoded_data = jwt_manager.verify_token(access_token)
#         print("Decoded Access Token Data:", decoded_data)
#     except Exception as e:
#         print(str(e))

#     # Verifying the refresh token
#     try:
#         decoded_refresh_data = jwt_manager.verify_token(refresh_token)
#         print("Decoded Refresh Token Data:", decoded_refresh_data)
#     except Exception as e:
#         print(str(e))

#     # Refreshing the access token using the refresh token
#     try:
#         new_access_token = jwt_manager.refresh_access_token(refresh_token)
#         print("New Access Token:", new_access_token)
#     except Exception as e:
#         print(str(e))
