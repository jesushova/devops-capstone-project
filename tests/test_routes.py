"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service.routes import app
from service import talisman  # Import Talisman

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"

# Define HTTPS environment overrides for testing
HTTPS_ENVIRON = {'wsgi.url_scheme': 'https'}


# Test cases
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        init_db(app)

        # Disable forced HTTPS
        talisman.force_https = False

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_list_accounts(self):
        """It should return a list of accounts"""
        # Create dummy accounts
        accounts = self._create_accounts(3)
        response = self.client.get(BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if response contains the list of created accounts
        returned_accounts = response.get_json()
        self.assertEqual(len(returned_accounts), 3)
        for returned_account, expected_account in zip(returned_accounts, accounts):
            self.assertEqual(returned_account["id"], expected_account.id)
            self.assertEqual(returned_account["name"], expected_account.name)
            self.assertEqual(returned_account["email"], expected_account.email)
            self.assertEqual(returned_account["address"], expected_account.address)
            self.assertEqual(returned_account["phone_number"], expected_account.phone_number)
            self.assertEqual(returned_account["date_joined"], str(expected_account.date_joined))

    def test_read_account(self):
        """It should read an existing account"""
        # Create a dummy account
        account = AccountFactory()
        response_create = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        new_account = response_create.get_json()

        # Read the created account
        response_read = self.client.get(f"{BASE_URL}/{new_account['id']}")
        self.assertEqual(response_read.status_code, status.HTTP_200_OK)
        returned_account = response_read.get_json()

        # Check if returned account matches the created one
        self.assertEqual(returned_account["id"], new_account["id"])
        self.assertEqual(returned_account["name"], account.name)
        self.assertEqual(returned_account["email"], account.email)
        self.assertEqual(returned_account["address"], account.address)
        self.assertEqual(returned_account["phone_number"], account.phone_number)
        self.assertEqual(returned_account["date_joined"], str(account.date_joined))

    def test_update_account(self):
        """It should update an existing account"""
        # Create a dummy account
        account = AccountFactory()
        response_create = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        new_account = response_create.get_json()

        # Update the created account
        updated_account_data = {
            "name": "Updated Name",
            "email": "updated_email@example.com",
            "address": "Updated Address",
            "phone_number": "1234567890"
        }
        response_update = self.client.put(
            f"{BASE_URL}/{new_account['id']}",
            json=updated_account_data,
            content_type="application/json"
        )
        self.assertEqual(response_update.status_code, status.HTTP_200_OK)
        updated_account = response_update.get_json()

        # Check if account was updated correctly
        self.assertEqual(updated_account["id"], new_account["id"])
        self.assertEqual(updated_account["name"], updated_account_data["name"])
        self.assertEqual(updated_account["email"], updated_account_data["email"])
        self.assertEqual(updated_account["address"], updated_account_data["address"])
        self.assertEqual(updated_account["phone_number"], updated_account_data["phone_number"])

    def test_delete_account(self):
        """It should delete an existing account"""
        # Create a dummy account
        account = AccountFactory()
        response_create = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        new_account = response_create.get_json()

        # Delete the created account
        response_delete = self.client.delete(f"{BASE_URL}/{new_account['id']}")
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)

        # Make sure account is deleted
        response_read = self.client.get(f"{BASE_URL}/{new_account['id']}")
        self.assertEqual(response_read.status_code, status.HTTP_404_NOT_FOUND)

    # New test cases added to increase code coverage
    def test_create_accounts_invalid_data(self):
        """It should not Create an Account when sending invalid data"""
        response = self.client.post(BASE_URL, data="invalid data")
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    def test_update_account_empty_data(self):
        """It should not Update an Account when sending empty data"""
        # Create a dummy account
        account = AccountFactory()
        response_create = self.client.post(BASE_URL, json=account.serialize())
        self.assertEqual(response_create.status_code, status.HTTP_201_CREATED)
        new_account = response_create.get_json()

        # Update the created account with empty data
        response_update = self.client.put(
            f"{BASE_URL}/{new_account['id']}",
            json={},
            content_type="application/json"
        )
        self.assertEqual(response_update.status_code, status.HTTP_400_BAD_REQUEST)

    def test_security_headers(self):
        """It should return security headers"""
        response = self.client.get('/', environ_overrides=HTTPS_ENVIRON)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        headers = {
            'X-Frame-Options': 'SAMEORIGIN',
            'X-Content-Type-Options': 'nosniff',
            'Content-Security-Policy': 'default-src \'self\'; object-src \'none\'',
            'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
        for key, value in headers.items():
            self.assertEqual(response.headers.get(key), value)


######################################################################
#   M A I N
######################################################################
if __name__ == "__main__":
    import unittest
    unittest.main()
