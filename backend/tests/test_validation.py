
import unittest

from app.validation import MAX_SESSION_ID_LENGTH, sanitize_id, validate_id


class TestValidation(unittest.TestCase):
    def test_basic_id(self):
        self.assertEqual(sanitize_id("valid-id_123"), "valid-id_123")

    def test_empty_id(self):
        self.assertEqual(sanitize_id(""), "default")
        self.assertEqual(sanitize_id(None), "default")

    def test_special_chars(self):
        self.assertEqual(sanitize_id("id with spaces"), "id_with_spaces")
        self.assertEqual(sanitize_id("id/with/slashes"), "id_with_slashes")
        # id (2) + 9 special chars = 11 chars. The 9 special chars become 9 underscores.
        self.assertEqual(sanitize_id("id@#$%^&*()"), "id_________")

    def test_leading_chars(self):
        # Should prepend "id_" if it starts with _ or .
        self.assertEqual(sanitize_id("_leading_underscore"), "id__leading_underscore")
        self.assertEqual(sanitize_id(".leading_dot"), "id__leading_dot")

    def test_very_long_id(self):
        long_id = "a" * (MAX_SESSION_ID_LENGTH + 10)
        sanitized = sanitize_id(long_id)
        self.assertEqual(len(sanitized), MAX_SESSION_ID_LENGTH)
        self.assertEqual(sanitized, "a" * MAX_SESSION_ID_LENGTH)

    def test_path_traversal_attempts(self):
        # ../../../etc/passwd -> 9 underscores + etc_passwd
        # starts with underscore, so prepends id_
        # id_ + 9 underscores + etc_passwd = id_ + 9 underscores + etc_passwd
        self.assertEqual(sanitize_id("../../../etc/passwd"), "id__________etc_passwd")
        self.assertEqual(sanitize_id(".."), "id___")

    def test_validate_id_valid(self):
        self.assertTrue(validate_id("valid-id_123"))

    def test_validate_id_invalid(self):
        with self.assertRaisesRegex(ValueError, "ID cannot be empty"):
            validate_id("")
        with self.assertRaisesRegex(ValueError, "invalid characters"):
            validate_id("id with spaces")
        with self.assertRaisesRegex(ValueError, "invalid characters"):
            validate_id("id/with/slashes")
        with self.assertRaisesRegex(ValueError, "invalid characters"):
            validate_id("id@#$%^&*()")
        with self.assertRaisesRegex(ValueError, "exceeds maximum length"):
            validate_id("a" * (MAX_SESSION_ID_LENGTH + 1))

if __name__ == "__main__":
    unittest.main()
