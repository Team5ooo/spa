import asyncio
import json
import hashlib
import hmac
import time
import secrets
import string
from aiohttp import ClientSession, ClientTimeout, ClientError

class MSPAAPI:
    def __init__(self, base_url, api_key=None, device_id=None, product_id=None, headers=None, session=None, timeout=5, username=None, password=None, access_token=None):
        self.base_url = base_url
        self.api_key = api_key
        self.device_id = device_id
        self.product_id = product_id
        self.headers = headers or {}
        self._timeout = timeout
        self.username = username
        self.password = password
        self._access_token = access_token  # Allow manual token input
        self._appid = "e1c8e068f9ca11eba4dc0242ac120002"  # Fixed app ID from const.py

        if session is None:
            self._session = ClientSession()
            self._cleanup_session = True
        else:
            self._session = session
            self._cleanup_session = False

    async def close(self):
        """Explicitly closes the ClientSession."""
        if not self._session.closed:
            await self._session.close()

    def __del__(self):
        """Handles cleanup, but no longer closes the session here."""
        if self._cleanup_session and not self._session.closed:
            asyncio.create_task(self._session.close())  # Schedule the close operation

    def _generate_nonce(self, length=32):
        """Generate a random nonce string."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def _generate_timestamp(self):
        """Generate current timestamp."""
        return str(int(time.time()))

    def _generate_signature(self, payload, nonce, timestamp, secret_key="87025c9ecd18906d27225fe79cb68349"):
        """Generate request signature using MD5 with app secret."""
        # Signature algorithm discovered from Android APK:
        # MD5(appId + ',' + appSecret + ',' + nonce + ',' + timestamp)
        message = f"{self._appid},{secret_key},{nonce},{timestamp}"
        signature = hashlib.md5(message.encode()).hexdigest().upper()
        return signature

    def _build_headers(self, payload=None):
        """Build request headers with proper authentication."""
        nonce = self._generate_nonce()
        timestamp = self._generate_timestamp()
        
        headers = {
            "push_type": "Android",
            "appid": self._appid,
            "nonce": nonce,
            "ts": timestamp,
            "lan_code": "en",
            "Content-Type": "application/json"
        }
        
        # Add authorization header
        if self._access_token:
            headers["authorization"] = f"token {self._access_token}"
        elif self.api_key:
            headers["authorization"] = f"token {self.api_key}"
        
        # Generate signature
        if payload:
            headers["sign"] = self._generate_signature(payload, nonce, timestamp)
        
        return headers

    def _build_login_headers(self, payload=None):
        """Build headers for initial login (with signature but no token)."""
        nonce = self._generate_nonce()
        timestamp = self._generate_timestamp()
        
        headers = {
            "push_type": "Android",
            "appid": self._appid,
            "nonce": nonce,
            "ts": timestamp,
            "lan_code": "en",
            "Content-Type": "application/json"
        }
        
        # Generate signature for login payload
        if payload:
            headers["sign"] = self._generate_signature(payload, nonce, timestamp)
        
        return headers

    async def login(self):
        """Authenticate with username/password to get access token."""
        if not self.username or not self.password:
            raise MSPAAPIException("Username and password required for authentication")
        
        # Hash password with MD5
        password_hash = hashlib.md5(self.password.encode()).hexdigest()
        
        # Generate a more realistic FCM-style registration ID
        registration_id = f"dummy_fcm_token_{secrets.token_urlsafe(32)[:50]}"
        
        login_payload = {
            "account": self.username,
            "app_id": self._appid,
            "password": password_hash,
            "brand": "",
            "registration_id": registration_id,
            "push_type": "android",
            "lan_code": "EN",
            "country": "US"  # Default, could be made configurable
        }
        
        try:
            url = f"{self.base_url.rstrip('/')}/enduser/get_token/"
            # Build headers WITH signature but WITHOUT token for login
            headers = self._build_login_headers(login_payload)
            
            resp = await self._session.post(
                url,
                headers=headers,
                json=login_payload,
                timeout=ClientTimeout(self._timeout),
            )
            
            data = await resp.json()
            
            # Check for successful response
            if data.get("code") == 0 or resp.status == 200:
                # Extract token from response
                token = data.get("data", {}).get("token") or data.get("token") or data.get("access_token")
                if token:
                    self._access_token = token
                    return True
            else:
                raise MSPAAPIException(f"Login failed: {data.get('message', 'Unknown error')}")
                    
        except MSPAAPIException:
            raise  # Re-raise our custom exceptions
        except Exception as e:
            raise MSPAAPIException(f"Login failed: {str(e)}")
        
        raise MSPAAPIException("Unable to authenticate with provided credentials")

    async def refresh_token(self):
        """Refresh the access token by logging in again."""
        if not self.username or not self.password:
            raise MSPAAPIException("Cannot refresh token without username and password")
        
        self._access_token = None  # Clear current token
        await self.login()

    async def _call_with_retry(self, endpoint, payload=None, retry_auth=True):
        """Make API call with automatic token refresh on authentication failure."""
        try:
            return await self._call_internal(endpoint, payload)
        except MSPAAPIException as e:
            # If authentication fails and we have credentials, try refreshing token
            if retry_auth and self.username and self.password and ("auth" in str(e).lower() or "token" in str(e).lower()):
                try:
                    await self.refresh_token()
                    return await self._call_internal(endpoint, payload)
                except MSPAAPIException:
                    # If refresh also fails, raise original error
                    raise e
            raise e

    async def _call_internal(self, endpoint, payload=None):
        """Internal method for making API calls without retry logic."""
        if self._session.closed:
            raise MSPAAPIException("Session already closed")

        # Auto-login if we have username/password but no token
        if self.username and self.password and not self._access_token and not self.api_key:
            await self.login()

        url = f"{self.base_url.rstrip('/')}/{endpoint}"
        headers = self._build_headers(payload)

        try:
            resp = await self._session.post(
                url,
                headers=headers,
                json=payload,
                timeout=ClientTimeout(self._timeout),
            )
            data = await resp.json()
            if data.get("code") != 0:  # Assuming 0 means success
                self._handle_error(data)
            else:
                return data  # Return the full response
        except ClientError as exc:
            raise MSPAAPIException("Unable to communicate with MSpa API") from exc
        except asyncio.TimeoutError as exc:
            raise MSPAAPIException("MSpa API request timed out") from exc

    async def _call(self, endpoint, payload=None):
        """Public API call method with automatic token refresh."""
        return await self._call_with_retry(endpoint, payload)


    async def get_device_status(self):
        payload = {
            "device_id": self.device_id,
            "product_id": self.product_id
        }
        response = await self._call("device/thing_shadow", payload)
        return response.get("data")
    
    async def send_device_command(self, desired_state):
        payload = {
            "desired": json.dumps({"state": {"desired": desired_state}}),
            "device_id": self.device_id,
            "product_id": self.product_id
        }
        return await self._call("device/command", payload)

    def _handle_error(self, data):
        error_msg = data.get("message", "MSpa API call failed")
        raise MSPAAPIException(error_msg)

    async def get_user_devices(self):
        """Get list of devices associated with the user account."""
        if not self._access_token:
            raise MSPAAPIException("No access token available. Please login first.")
        
        try:
            # Use GET request with token authentication and signature
            url = f"{self.base_url.rstrip('/')}/enduser/devices/"
            headers = self._build_headers()  # This will include token and signature
            
            resp = await self._session.get(
                url,
                headers=headers,
                timeout=ClientTimeout(self._timeout),
            )
            
            data = await resp.json()
            
            if data.get("code") != 0:
                raise MSPAAPIException(f"Failed to get devices: {data.get('message', 'Unknown error')}")
            
            devices = data.get("data", {}).get("list", [])
            
            # Extract relevant device information
            device_list = []
            for device in devices:
                device_info = {
                    "device_id": device.get("device_id"),
                    "product_id": device.get("product_id"),
                    "name": device.get("name") or device.get("device_alias"),
                    "product_model": device.get("product_model"),
                    "is_online": device.get("is_online", False),
                    "is_connect": device.get("is_connect", False),
                    "mac": device.get("mac"),
                    "sn": device.get("sn")
                }
                device_list.append(device_info)
            
            return device_list
        except MSPAAPIException:
            raise
        except Exception as e:
            raise MSPAAPIException(f"Failed to get user devices: {str(e)}")

    async def test_connection(self):
        payload = {
            "device_id": self.device_id,
            "product_id": self.product_id
        }
        try:
            await self._call("device/thing_shadow", payload)
            return True
        except MSPAAPIException:
            return False # or raise the exception again, depending on your needs

class MSPAAPIException(Exception):
    def __init__(self, message) -> None:
        self.message = message

    def __str__(self):
        return self.message
